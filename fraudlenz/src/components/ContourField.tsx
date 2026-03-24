function buildContourPath(index: number, width: number, height: number, drift: number) {
  const segments = 7
  const baseY = height * 0.36 + index * 12
  const segmentWidth = width / segments
  let path = `M -80 ${baseY.toFixed(1)}`

  for (let segment = 0; segment < segments + 1; segment += 1) {
    const x1 = segment * segmentWidth
    const x2 = x1 + segmentWidth / 2
    const x3 = x1 + segmentWidth
    const amplitudeA =
      Math.sin(index * 0.28 + segment * 0.65 + drift) * 36 +
      Math.cos(segment * 0.45 + drift) * 18
    const amplitudeB =
      Math.cos(index * 0.22 + segment * 0.58 + drift) * 44 +
      Math.sin(segment * 0.72 + drift) * 14

    path += ` C ${x1.toFixed(1)} ${(baseY - amplitudeA).toFixed(1)} ${x2.toFixed(1)} ${(baseY + amplitudeB).toFixed(1)} ${x3.toFixed(1)} ${baseY.toFixed(1)}`
  }

  return path
}

type ContourFieldProps = {
  className?: string
  height?: number
  drift?: number
}

export function ContourField({
  className,
  height = 760,
  drift = 0,
}: ContourFieldProps) {
  const paths = Array.from({ length: 48 }, (_, index) =>
    buildContourPath(index, 1440, height, drift),
  )

  return (
    <svg
      className={className}
      viewBox={`0 0 1440 ${height}`}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      {paths.map((path, index) => (
        <path key={`${drift}-${index}`} d={path} />
      ))}
    </svg>
  )
}
