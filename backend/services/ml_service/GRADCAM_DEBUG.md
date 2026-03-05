# Grad-CAM Target Layer Selection Guide

## The Target Layer Problem

Grad-CAM needs to know **exactly which layer** of the neural network to analyze. Choosing the wrong layer results in:
- Solid blue/red squares instead of meaningful heatmaps
- Random noise patterns
- No visualization at all

## Correct Target Layers by Architecture

### EfficientNet (timm library)

**For EfficientNet-B0 to B7:**
```python
# Option 1: Last block (RECOMMENDED)
target_layer = model.blocks[-1]

# Option 2: Within last block
target_layer = model.blocks[-1][-1]  # Last layer of last block

# Option 3: Conv head (alternative)
target_layer = model.conv_head
```

**Our Implementation (EfficientNet-B3):**
```python
from core.xai_engine import get_explainer

explainer = get_explainer()
heatmap, base64_img = explainer.generate_heatmap(
    model=fundus_model,
    input_tensor=image_tensor,
    target_layer=fundus_model.blocks[-1],  # ✓ Correct for EfficientNet
    original_image=rgb_image
)
```

### Vision Transformer (ViT)

**For google/vit-base-patch16-224:**
```python
# Option 1: Last encoder block normalization
target_layer = model.vit.encoder.layer[-1].layernorm_before

# Option 2: Last attention layer
target_layer = model.vit.encoder.layer[-1].attention.attention

# Option 3: Entire last block
target_layer = model.vit.encoder.layer[-1]
```

**Note:** ViT requires special handling because it uses attention mechanisms instead of convolutions.

### ResNet Models

```python
# For ResNet-50, ResNet-101, etc.
target_layer = model.layer4[-1]  # Last layer of layer4
```

### VGG Models

```python
# For VGG16, VGG19
target_layer = model.features[-1]  # Last convolutional layer
```

## Auto-Detection in Our XAI Engine

Our `VisualExplainer` automatically detects the target layer:

```python
def _get_target_layer(self, model: nn.Module) -> nn.Module:
    """Auto-detect target layer"""
    
    # EfficientNet (timm)
    if hasattr(model, 'blocks'):
        return model.blocks[-1]  # ✓
    
    # VGG, ResNet with 'features'
    elif hasattr(model, 'features'):
        return model.features[-1]
    
    # ResNet with layer4
    elif hasattr(model, 'layer4'):
        return model.layer4[-1]
    
    # Generic: find last Conv2d
    else:
        for module in reversed(list(model.modules())):
            if isinstance(module, nn.Conv2d):
                return module
```

## Debugging Solid Color Heatmaps

### Symptom: Solid blue/red square

**Problem:** Wrong target layer selected

**Solution:**
1. Print model architecture:
```python
print(model)
```

2. Find the last convolutional layer name

3. Manually specify:
```python
# Get the specific layer by name
target_layer = model.blocks[6]  # For EfficientNet-B3
```

### Symptom: Random noise pattern

**Problem:** Layer is too early in the network

**Solution:** Use a later layer (closer to output)

### Symptom: No heatmap at all

**Problem:** 
- Layer doesn't have gradients
- Model in train mode instead of eval mode

**Solution:**
```python
model.eval()  # Ensure eval mode
with torch.no_grad():  # For inference
    # But Grad-CAM needs gradients!
# Don't use torch.no_grad() for Grad-CAM!
```

## Testing Your Target Layer

```python
import torch
from pytorch_grad_cam import GradCAM

# Test if layer works
try:
    cam = GradCAM(
        model=your_model,
        target_layers=[your_target_layer],
        use_cuda=False
    )
    
    # Test with dummy input
    dummy_input = torch.randn(1, 3, 224, 224)
    grayscale_cam = cam(dummy_input)
    
    print("✓ Target layer works!")
    print(f"Output shape: {grayscale_cam.shape}")
    
except Exception as e:
    print(f"✗ Target layer failed: {e}")
```

## Model-Specific Recommendations

### Refracto AI Services

**Fundus Model (EfficientNet-B3):**
```python
target_layer = fundus_model.blocks[-1]  # ✓ Confirmed working
```

**OCT Model (ViT):**
```python
# ViT requires special attention
target_layer = oct_model.vit.encoder.layer[-1].layernorm_before
```

**Refraction Model (EfficientNet-B0):**
```python
target_layer = refraction_backbone.blocks[-1]  # ✓ Confirmed working
```

## Common Mistakes

❌ **Wrong:**
```python
target_layer = model  # Too broad
target_layer = model.classifier  # Not a conv layer
target_layer = model.blocks[0]  # Too early
```

✅ **Correct:**
```python
target_layer = model.blocks[-1]  # Last convolutional block
target_layer = model.blocks[-1][-1]  # Last layer in last block
```

## Verifying Your Heatmap

A **good heatmap** should:
- ✅ Show varying intensity (not solid color)
- ✅ Highlight specific regions (not uniform)
- ✅ Make clinical sense (e.g., optic disc for glaucoma)
- ✅ Change when you change the target class

A **bad heatmap** indicates:
- ❌ Wrong layer selected
- ❌ Model not properly initialized
- ❌ Input preprocessing issues

## Quick Reference Commands

**Find available layers:**
```python
for name, module in model.named_modules():
    if isinstance(module, nn.Conv2d):
        print(f"Conv layer: {name}")
```

**Test multiple layers:**
```python
layer_candidates = [
    model.blocks[-1],
    model.blocks[-2],
    model.conv_head
]

for layer in layer_candidates:
    try:
        explainer.generate_heatmap(model, input_tensor, target_layer=layer)
        print(f"✓ Layer {layer} works!")
    except:
        print(f"✗ Layer {layer} failed")
```

## Production Checklist

Before deploying Grad-CAM:

- [ ] Verify target layer with test images
- [ ] Check heatmaps make clinical sense
- [ ] Test with different disease classes
- [ ] Ensure CPU/GPU compatibility
- [ ] Monitor performance (Grad-CAM can be slow)
- [ ] Add error handling for edge cases

---

**Remember:** When in doubt, use `model.blocks[-1]` for timm models! 🎯
