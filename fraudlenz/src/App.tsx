import { Navigate, Route, Routes } from 'react-router-dom'
import './styles/site.css'
import { useRevealOnScroll } from './hooks/useRevealOnScroll'
import { AppLayout } from './components/AppLayout'
import { HomePage } from './pages/HomePage'
import { ResultsPage } from './pages/ResultsPage'
import { UploadPage } from './pages/UploadPage'

function App() {
  useRevealOnScroll()

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/results/:fileId" element={<ResultsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
