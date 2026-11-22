import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './App.css'
import WorkspacePage from '../pages/WorkspacePage.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <WorkspacePage />
  </StrictMode>,
)
