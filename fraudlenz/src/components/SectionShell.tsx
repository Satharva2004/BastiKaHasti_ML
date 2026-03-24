import type { ReactNode } from 'react'
import { ContourField } from './ContourField'

type SectionShellProps = {
  id: string
  className?: string
  innerClassName?: string
  contourClassName?: string
  contourDrift?: number
  contourHeight?: number
  children: ReactNode
}

export function SectionShell({
  id,
  className,
  innerClassName,
  contourClassName,
  contourDrift = 0,
  contourHeight,
  children,
}: SectionShellProps) {
  return (
    <section className={['section', className].filter(Boolean).join(' ')} id={id}>
      {contourClassName ? (
        <ContourField
          className={['contour', contourClassName].filter(Boolean).join(' ')}
          drift={contourDrift}
          height={contourHeight}
        />
      ) : null}
      <div className={['section__inner', innerClassName].filter(Boolean).join(' ')}>
        {children}
      </div>
    </section>
  )
}
