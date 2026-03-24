type LogoProps = {
  as?: 'a' | 'div'
  href?: string
  className?: string
}

export function Logo({ as = 'div', href, className }: LogoProps) {
  const classNames = ['brand', className].filter(Boolean).join(' ')

  if (as === 'a') {
    return (
      <a className={classNames} href={href}>
        <span className="brand__mark" />
        <span className="brand__text">FraudLens</span>
      </a>
    )
  }

  return (
    <div className={classNames}>
      <span className="brand__mark" />
      <span className="brand__text">FraudLens</span>
    </div>
  )
}
