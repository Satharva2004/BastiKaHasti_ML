type SectionIntroProps = {
  eyebrow: string
  title: string
  copy?: string
  delay?: string
  className?: string
}

export function SectionIntro({
  eyebrow,
  title,
  copy,
  delay = '0ms',
  className,
}: SectionIntroProps) {
  return (
    <div
      className={['reveal', className].filter(Boolean).join(' ')}
      data-reveal
      style={{ ['--delay' as string]: delay }}
    >
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {copy ? <p className="section-copy">{copy}</p> : null}
    </div>
  )
}
