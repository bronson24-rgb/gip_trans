import { GoogleOAuthProvider } from '@react-oauth/google'
import { AuthGate } from './AuthGate'
import { DriverReportForm } from './DriverReportForm'
import './App.css'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? ''

function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthGate>
        <DriverReportForm />
      </AuthGate>
    </GoogleOAuthProvider>
  )
}

export default App
