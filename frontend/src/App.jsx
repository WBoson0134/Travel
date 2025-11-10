import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import TripGenerator from './components/TripGenerator'
import TripView from './components/TripView'
import TripMap from './components/TripMap'
import Navbar from './components/Navbar'
import AIAssistant from './components/AIAssistant'
import Settings from './components/Settings'

const theme = createTheme({
  palette: {
    primary: {
      main: '#3498db',
    },
    secondary: {
      main: '#2ecc71',
    },
  },
})

function App() {
  const [currentTrip, setCurrentTrip] = useState(null)

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Navbar />
        <Routes>
          <Route 
            path="/" 
            element={<TripGenerator onTripGenerated={setCurrentTrip} />} 
          />
          <Route 
            path="/trip/:id" 
            element={<TripView />} 
          />
          <Route 
            path="/trip-result" 
            element={<TripView />} 
          />
          <Route 
            path="/trip/:id/map" 
            element={<TripMap />} 
          />
          <Route 
            path="/ai-assistant" 
            element={<AIAssistant />} 
          />
          <Route 
            path="/settings" 
            element={<Settings />} 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ThemeProvider>
  )
}

export default App

