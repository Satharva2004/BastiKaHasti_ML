import { Logo } from '../components/Logo'

export function SiteFooter() {
  return (
    <footer className="site-footer" id="footer">
      <Logo className="site-footer__brand" />
      <p className="site-footer__copy">
        Real-time transaction fraud detection · Powered by LightGBM + SHAP · Built
        for India&apos;s financial stack
      </p>
      <p className="site-footer__meta">© 2024 FraudLens · All rights reserved</p>
    </footer>
  )
}
