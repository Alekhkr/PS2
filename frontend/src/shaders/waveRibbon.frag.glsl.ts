/**
 * GLSL Fragment Shader for Austensor EXP_07 Harmonic Ribbon Tubes.
 * Computes continuous spectral chrominance (neon gradient), Fresnel edge glow,
 * elevation-driven luminance, and selective Bloom emission.
 */
export const waveRibbonFragmentShader = /* glsl */ `
uniform vec3 uColorA;
uniform vec3 uColorB;
uniform vec3 uColorC;
uniform vec3 uColorD;
uniform float uAudioLevel;
uniform float uTime;

varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vWorldPosition;
varying float vElevation;
varying float vRibbonFactor;

// Cosine based palette generator (Inigo Quilez)
vec3 spectralPalette(float t) {
    vec3 a = vec3(0.5, 0.5, 0.5);
    vec3 b = vec3(0.5, 0.5, 0.5);
    vec3 c = vec3(1.0, 1.0, 1.0);
    vec3 d = vec3(0.00, 0.33, 0.67);
    return a + b * cos(6.28318 * (c * t + d));
}

void main() {
    // View direction vector in world space
    vec3 viewDir = normalize(cameraPosition - vWorldPosition);
    vec3 norm = normalize(vNormal);

    // Fresnel glow intensity
    float NdotV = max(0.0, dot(norm, viewDir));
    float fresnel = pow(1.0 - NdotV, 2.8);

    // Continuous spectral chrominance
    float tColor = fract(vRibbonFactor * 1.1 + vElevation * 0.12 + uTime * 0.02);
    vec3 baseColor = spectralPalette(tColor);

    // Elevation gradient highlights
    float elevationFactor = smoothstep(-1.5, 2.0, vElevation);
    vec3 highlightColor = mix(uColorA, uColorB, elevationFactor);

    // Combine base spectral palette with highlights and Fresnel rim
    vec3 finalColor = mix(baseColor, highlightColor, 0.45);
    finalColor += fresnel * uColorA * (1.6 + uAudioLevel * 1.2);

    // Selective emission for UnrealBloomPass
    float emission = (fresnel * 1.8 + abs(vElevation) * 0.35 + uAudioLevel * 0.5);
    finalColor *= emission;

    // Atmospheric depth falloff to deep void black (#000000)
    float dist = length(cameraPosition - vWorldPosition);
    float fogFactor = smoothstep(10.0, 36.0, dist);
    finalColor = mix(finalColor, vec3(0.0, 0.0, 0.0), fogFactor);

    gl_FragColor = vec4(finalColor, 0.95);
}
`;
