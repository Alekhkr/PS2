/**
 * GLSL Vertex Displacement Shader for Austensor EXP_07 Harmonic Ribbon Tubes.
 * Implements multi-frequency Fourier sine superposition, spatial Gaussian damping,
 * and localized pointer-induced phase interference ripples.
 */
export const waveRibbonVertexShader = /* glsl */ `
uniform float uTime;
uniform float uSpeed;
uniform float uAudioLevel;
uniform float uScrollProgress;
uniform vec2 uPointer;
uniform float uPointerIntensity;
uniform float uRibbonIndex;

varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vWorldPosition;
varying float vElevation;
varying float vRibbonFactor;

void main() {
    vUv = uv;
    vNormal = normal;

    vec3 pos = position;
    float ribbonRatio = uRibbonIndex / 14.0;
    vRibbonFactor = ribbonRatio;

    // Phase offset per ribbon
    float phaseOffset = ribbonRatio * 1.5707963; // pi/2 dispersion
    float speed = uSpeed * (1.0 + uAudioLevel * 0.45);
    float t = uTime * speed;

    // Gaussian spatial damping: exp(-alpha * x^2)
    float spatialDamping = exp(-0.016 * pos.x * pos.x);

    // Multi-Harmonic Fourier Superposition (4 fundamental modes)
    float wave1 = 1.35 * sin(0.38 * pos.x + t + phaseOffset);
    float wave2 = 0.65 * sin(0.92 * pos.x - t * 0.75 + phaseOffset * 1.618);
    float wave3 = 0.32 * sin(1.85 * pos.x + t * 1.35 + ribbonRatio * 3.14159);
    float wave4 = 0.16 * sin(3.40 * pos.x - t * 2.10);

    // Pointer-induced phase interference node
    float distToPointer = distance(vec2(pos.x, pos.z), uPointer * vec2(12.0, 6.0));
    float pointerInterference = sin(distToPointer * 2.2 - t * 3.5) * exp(-0.45 * distToPointer) * uPointerIntensity * 1.8;

    // Total displacement along Y
    float totalElevation = (wave1 + wave2 + wave3 + wave4 + pointerInterference) * spatialDamping;

    // Audio resonance amplification on central ribbons
    float audioBoost = 1.0 + (sin(ribbonRatio * 3.14159) * uAudioLevel * 0.8);
    totalElevation *= audioBoost;

    // Scroll-linked depth deformation
    pos.y += totalElevation;
    pos.z += sin(pos.x * 0.15 + t * 0.3) * (uScrollProgress * 1.5);

    vElevation = totalElevation;

    vec4 worldPos = modelMatrix * vec4(pos, 1.0);
    vWorldPosition = worldPos.xyz;

    gl_Position = projectionMatrix * viewMatrix * worldPos;
}
`;
