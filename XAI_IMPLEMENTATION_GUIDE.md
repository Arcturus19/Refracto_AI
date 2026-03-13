# XAI (Explainable AI) Interface Implementation Guide

## Overview

The XAI interface provides comprehensive explainability for all AI predictions in the Refracto dashboard. It includes:
- **Visual explanations** (attention maps, saliency maps)
- **Textual explanations** (human-readable reasoning)
- **Feature importance** (what influenced the prediction)
- **Confidence breakdown** (decomposition by source)
- **Uncertainty quantification** (prediction reliability)

---

## Backend Components

### 1. XAI Explainability Engine (`xai_explainability.py`)

Core Python module providing all explanation generation.

#### Key Classes

**ExplanationResult**
```python
@dataclass
class ExplanationResult:
    prediction_id: str
    task: str  # 'DR', 'Glaucoma', 'Refraction'
    prediction_value: any
    confidence: float
    attention_map: Optional[np.ndarray]
    saliency_map: Optional[np.ndarray]
    feature_importance: Dict[str, float]
    explanation_text: str
    reasoning_steps: List[str]
    class_probabilities: Dict[str, float]
    confidence_sources: Dict[str, float]
    prediction_uncertainty: float
    confidence_level: str  # 'high', 'medium', 'low'
```

**GradCAMExplainer**
Generate attention maps showing which image regions influenced predictions.
```python
explainer = GradCAMExplainer(model, target_layer='layer4')
attention_map = explainer.generate_attention_map(image, class_idx)
saliency_map = explainer.generate_saliency_map(image)
```

**FeatureImportanceExplainer**
Calculate permutation importance scores for features.
```python
importance = FeatureImportanceExplainer(model)
scores = importance.compute_importance(features, baseline_score)
top_k = importance.get_top_features(scores, top_k=5)
```

**ExplanationGenerator**
Create human-readable text explanations.
```python
generator = ExplanationGenerator()

# DR Explanation
text, steps = generator.generate_dr_explanation(
    prediction=2,
    confidence=0.87,
    class_probabilities=probs
)

# Glaucoma Explanation
text, steps = generator.generate_glaucoma_explanation(
    prediction=0.65,
    confidence=0.75,
    correction_factor=1.2
)

# Refraction Explanation
text, steps = generator.generate_refraction_explanation(
    sphere=-2.5,
    cylinder=-0.75,
    axis=90,
    confidence=0.82
)
```

**UncertaintyQuantifier**
Estimate prediction uncertainty using entropy.
```python
quantifier = UncertaintyQuantifier()
uncertainty, level = quantifier.compute_uncertainty(class_probs)
sources = quantifier.compute_confidence_sources(logits, modality_scores)
```

**XAIExplainabilityEngine**
Main orchestrator combining all components.
```python
engine = XAIExplainabilityEngine(model)

# Get DR explanation
result = engine.explain_dr_prediction(
    prediction_id="pred_123",
    dr_prediction=1,
    confidence=0.82,
    class_probabilities={"No DR": 0.18, "Mild": 0.82, ...}
)

# Get glaucoma explanation
result = engine.explain_glaucoma_prediction(
    prediction_id="pred_123",
    glaucoma_score=0.45,
    confidence=0.76,
    myopia_correction=1.15
)

# Get refraction explanation
result = engine.explain_refraction_prediction(
    prediction_id="pred_123",
    sphere=-1.5,
    cylinder=-0.5,
    axis=75,
    confidence=0.81
)
```

---

### 2. XAI API Routes (`xai_api_routes.py`)

REST endpoints for explanation generation.

#### Endpoints

**POST `/api/ml/xai/explain/dr`**
Generate DR prediction explanation.

Request:
```json
{
  "prediction_id": "pred_123",
  "dr_prediction": 1,
  "confidence": 0.85,
  "class_probabilities": {
    "No DR": 0.15,
    "Mild": 0.85,
    "Moderate": 0.0,
    "Severe": 0.0,
    "Proliferative": 0.0
  }
}
```

Response:
```json
{
  "prediction_id": "pred_123",
  "task": "DR",
  "prediction_value": 1,
  "confidence": 0.85,
  "explanation_text": "The model predicts Mild diabetic retinopathy with high confidence (85.0%).",
  "reasoning_steps": [
    "Primary prediction: Mild",
    "Confidence level: 85.0%",
    "Model certainty: with high confidence"
  ],
  "confidence_level": "high",
  "prediction_uncertainty": 0.15,
  "class_probabilities": {
    "No DR": 0.15,
    "Mild": 0.85,
    "Moderate": 0.0,
    "Severe": 0.0,
    "Proliferative": 0.0
  },
  "confidence_sources": {
    "fundus": 0.6,
    "oct": 0.4
  }
}
```

**POST `/api/ml/xai/explain/glaucoma`**
Generate glaucoma prediction explanation.

**POST `/api/ml/xai/explain/refraction`**
Generate refraction prediction explanation.

**GET `/api/ml/xai/feature-importance/dr`**
Get top features influencing DR predictions globally.

Response:
```json
{
  "task": "DR",
  "top_features": [
    {
      "feature": "microaneurysms_count",
      "importance": 0.95,
      "description": "Count of microaneurysms visible in fundus image"
    },
    {
      "feature": "hemorrhage_area",
      "importance": 0.88,
      "description": "Total area of hemorrhages detected"
    }
  ]
}
```

**GET `/api/ml/xai/interpretation-guide`**
Get guidance on interpreting XAI results.

**POST `/api/ml/xai/batch-explain`**
Generate explanations for multiple predictions.

---

## Frontend Components

### 1. ExplanationComponents (`ExplanationComponents.tsx`)

Reusable React components for displaying explanations.

#### Components

**ExplanationPanel**
Displays text explanation and reasoning steps.
```tsx
import { ExplanationPanel } from '@/components/XAI/ExplanationComponents';

<ExplanationPanel explanation={explanationData} />
```

Features:
- Main explanation text with confidence badge
- Numbered reasoning steps
- Class probability distribution
- Confidence level color coding

**AttentionMapViewer**
Visualizes attention/saliency maps.
```tsx
import { AttentionMapViewer } from '@/components/XAI/ExplanationComponents';

<AttentionMapViewer mapData={base64EncodedMap} mapType="attention" />
```

Features:
- Red-blue color scale (red = high influence)
- Loading state handling
- Map type label (attention/saliency)

**FeatureImportanceChart**
Shows feature importance as horizontal bars.
```tsx
import { FeatureImportanceChart } from '@/components/XAI/ExplanationComponents';

<FeatureImportanceChart features={topFeatures} />
```

Features:
- Feature names with human-readable labels
- Importance percentage
- Gradient bar visualization
- Top-K feature filtering

**ConfidenceBreakdown**
Decompose confidence by source (modality, feature).
```tsx
import { ConfidenceBreakdown } from '@/components/XAI/ExplanationComponents';

<ConfidenceBreakdown 
  sources={{ fundus: 0.6, oct: 0.4 }} 
  uncertainty={0.15} 
/>
```

Features:
- Overall confidence gauge
- Source contribution breakdown
- Uncertainty indication
- Color-coded confidence levels

**XAIModal**
Comprehensive modal with tabbed interface.
```tsx
import { XAIModal } from '@/components/XAI/ExplanationComponents';

<XAIModal
  isOpen={true}
  onClose={() => setIsOpen(false)}
  explanation={explanationData}
  attendionMapData={mapData}
/>
```

Tabs:
1. **Explanation** - Text and reasoning
2. **Features** - Feature importance
3. **Confidence** - Confidence breakdown
4. **Visual** - Attention maps

**XAIInfoBanner**
Compact banner showing XAI summary.
```tsx
import { XAIInfoBanner } from '@/components/XAI/ExplanationComponents';

<XAIInfoBanner 
  explanation={explanationData} 
  onExplore={() => setShowModal(true)} 
/>
```

---

### 2. Enhanced Results Panel (`MTLResultsPanelWithXAI.tsx`)

Integrated component showing predictions with XAI.

```tsx
import { MTLResultsPanelWithXAI } from '@/components/XAI/MTLResultsPanelWithXAI';

const results = {
  prediction_id: "pred_123",
  dr_prediction: 1,
  glaucoma_prediction: 0.45,
  refraction_sphere: -2.5,
  refraction_cylinder: -0.75,
  refraction_axis: 90,
  dr_confidence: 0.85,
  glaucoma_confidence: 0.72,
  refraction_confidence: 0.81,
  dr_classes: {
    "No DR": 0.15,
    "Mild": 0.85,
    "Moderate": 0.0,
    "Severe": 0.0,
    "Proliferative": 0.0
  }
};

<MTLResultsPanelWithXAI 
  results={results}
  onRequestReview={(predId) => console.log('Review:', predId)}
/>
```

Features:
- Collapsible sections for each task
- Quick XAI info banners
- Lazy-loaded explanations
- Low confidence warnings
- "View AI Explanation" buttons

---

## Integration Guide

### Step 1: Install Backend Module

Import in `main.py`:
```python
from xai_api_routes import router as xai_router
from xai_explainability import XAIExplainabilityEngine

app.include_router(xai_router)

# Initialize XAI engine
xai_engine = XAIExplainabilityEngine(model)
```

### Step 2: Update Analysis Endpoint

When returning predictions, include explanation:
```python
@app.post("/api/ml/analyze/mtl")
async def analyze_mtl(files: UploadFile):
    # ... existing code ...
    
    # Generate predictions
    predictions = model.predict(images)
    
    # Generate explanations
    explanation = xai_engine.explain_dr_prediction(
        prediction_id=audit_id,
        dr_prediction=predictions['dr'],
        confidence=predictions['dr_confidence'],
        class_probabilities=predictions['dr_probs']
    )
    
    # Store explanation
    # db.add(Explanation(**explanation.to_dict()))
    
    return {
        ...predictions,
        "explanation": explanation.to_dict()
    }
```

### Step 3: Update Frontend Components

Replace MTLResultsPanel with XAI version:
```tsx
// Before
import { MTLResultsPanel } from '@/components/MTLResultsPanel';

// After
import { MTLResultsPanelWithXAI } from '@/components/XAI/MTLResultsPanelWithXAI';
```

### Step 4: Add to Dashboard Routes

Update AnalysisPage to use new component:
```tsx
import { MTLResultsPanelWithXAI } from '@/components/XAI/MTLResultsPanelWithXAI';

export const AnalysisPage: React.FC = () => {
  return (
    <div>
      {results && (
        <MTLResultsPanelWithXAI 
          results={results}
          onRequestReview={handleReview}
        />
      )}
    </div>
  );
};
```

---

## Database Schema

Store explanations in database:
```sql
CREATE TABLE explanations (
    id SERIAL PRIMARY KEY,
    prediction_id UUID NOT NULL REFERENCES audit_logs(id),
    task VARCHAR(50) NOT NULL,  -- 'DR', 'Glaucoma', 'Refraction'
    prediction_value FLOAT,
    confidence FLOAT,
    explanation_text TEXT,
    reasoning_steps JSONB,
    feature_importance JSONB,
    class_probabilities JSONB,
    confidence_sources JSONB,
    prediction_uncertainty FLOAT,
    confidence_level VARCHAR(20),
    attention_map_base64 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES audit_logs(id)
);

CREATE INDEX idx_explanations_prediction ON explanations(prediction_id);
CREATE INDEX idx_explanations_task ON explanations(task);
```

---

## Usage Examples

### Example 1: Display DR Prediction with Explanation

```tsx
const [explanation, setExplanation] = useState(null);

const fetchExplanation = async (predictionId) => {
  const response = await fetch('/api/ml/xai/explain/dr', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prediction_id: predictionId,
      dr_prediction: 1,
      confidence: 0.85,
      class_probabilities: { "Mild": 0.85, ... }
    })
  });
  
  const data = await response.json();
  setExplanation(data);
};

// In component
<XAIModal
  isOpen={showModal}
  onClose={() => setShowModal(false)}
  explanation={explanation}
/>
```

### Example 2: Feature Importance in Report

```tsx
const [features, setFeatures] = useState([]);

useEffect(() => {
  fetch('/api/ml/xai/feature-importance/dr')
    .then(r => r.json())
    .then(data => setFeatures(data.top_features));
}, []);

<FeatureImportanceChart features={features} />
```

### Example 3: Batch Explanations

```python
predictions = [
    {
        "task": "DR",
        "prediction_id": "pred_1",
        "dr_prediction": 0,
        "confidence": 0.92
    },
    {
        "task": "Glaucoma",
        "prediction_id": "pred_2",
        "glaucoma_score": 0.34,
        "confidence": 0.81
    }
]

response = requests.post(
    'http://localhost:8000/api/ml/xai/batch-explain',
    json=predictions
)

explanations = response.json()['explanations']
```

---

## Best Practices

### For Developers

1. **Cache explanations**: Fetch once, reuse for modal tabs
2. **Error handling**: Fall back to basic explanation if XAI fails
3. **Performance**: Load explanations on-demand (lazy loading)
4. **Accessibility**: Include alt text for visual maps

### For Clinicians

1. **High confidence (≥85%)**: Safe for clinical use
2. **Medium confidence (70-85%)**: Review with clinical judgment
3. **Low confidence (<70%)**: Require expert review
4. **Feature importance**: Check if model focused on relevant features
5. **Attention maps**: Verify red regions align with clinical findings

---

## Troubleshooting

### Explanation Not Generated
- Check prediction confidence is valid (0-1)
- Verify class probabilities sum to 1.0
- Check for errors in model inference

### Attention Maps Black
- Ensure image is normalized correctly
- Check model layer hooks registered
- Verify model is in eval mode

### High Uncertainty Even for Correct Predictions
- May indicate insufficient training data
- Consider retraining with more examples
- Check input preprocessing

---

## Future Enhancements

1. **SHAP Explanations**: More sophisticated feature attribution
2. **Counterfactual Explanations**: "What if" scenarios
3. **Model Comparison**: Compare predictions across multiple models
4. **Explanation Validation**: Expert review of explanations
5. **Real-time Visualization**: Interactive attention map exploration

---

## References

- Grad-CAM: https://arxiv.org/abs/1610.02055
- LIME: https://arxiv.org/abs/1602.04938
- SHAP: https://arxiv.org/abs/1705.07874
