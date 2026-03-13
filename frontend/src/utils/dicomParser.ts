import * as daikon from 'daikon';

export const generateDicomPreview = async (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();

        reader.onload = (event) => {
            try {
                const arrayBuffer = event.target?.result as ArrayBuffer;
                if (!arrayBuffer) {
                    reject(new Error("Failed to read file"));
                    return;
                }

                // Parse the DICOM file using daikon
                const dataView = new DataView(arrayBuffer);
                const image = daikon.Series.parseImage(dataView);
                
                if (!image) {
                     reject(new Error("Could not parse DICOM image"));
                     return;
                }

                if (!image.hasPixelData()) {
                     reject(new Error("DICOM file has no pixel data"));
                     return;
                }

                // Build an offscreen canvas to render the image
                const canvas = document.createElement('canvas');
                canvas.width = image.getCols();
                canvas.height = image.getRows();
                const ctx = canvas.getContext('2d');
                
                if (!ctx) {
                    reject(new Error("Could not get canvas context"));
                    return;
                }

                // Get interpreted data as an object to get min/max for normalization
                const interpreted = image.getInterpretedData(false, true) as { data: Float32Array; min: number; max: number };
                const rawData = interpreted.data;
                const min = interpreted.min;
                const max = interpreted.max;
                
                const imageData = ctx.createImageData(canvas.width, canvas.height);
                const range = max - min || 1; // Avoid division by zero
                
                for (let i = 0; i < rawData.length; i++) {
                    const value = rawData[i];
                    // Normalize to 0-255 based on min/max
                    let normalized = ((value - min) / range) * 255;
                    normalized = Math.min(255, Math.max(0, normalized)); // Clamp
                    
                    const index = i * 4;
                    imageData.data[index] = normalized;     // R
                    imageData.data[index + 1] = normalized; // G
                    imageData.data[index + 2] = normalized; // B
                    imageData.data[index + 3] = 255;        // A
                }

                ctx.putImageData(imageData, 0, 0);
                
                // Convert canvas to base64 data URL
                const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
                resolve(dataUrl);

            } catch (err) {
                console.error("Error parsing DICOM:", err);
                reject(err);
            }
        };

        reader.onerror = (err) => {
            console.error("FileReader error:", err);
            reject(err);
        };

        reader.readAsArrayBuffer(file);
    });
};
