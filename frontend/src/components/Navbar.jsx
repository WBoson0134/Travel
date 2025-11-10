import React from 'react'
import { AppBar, Toolbar, Typography, Button } from '@mui/material'
import { useNavigate, useLocation } from 'react-router-dom'

function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          智能行程生成系统
        </Typography>
        <Button 
          color="inherit" 
          onClick={() => navigate('/')}
          variant={location.pathname === '/' ? 'outlined' : 'text'}
        >
          生成行程
        </Button>
        <Button 
          color="inherit" 
          onClick={() => navigate('/ai-assistant')}
          variant={location.pathname === '/ai-assistant' ? 'outlined' : 'text'}
        >
          AI助手
        </Button>
        <Button 
          color="inherit" 
          onClick={() => navigate('/settings')}
          variant={location.pathname === '/settings' ? 'outlined' : 'text'}
        >
          设置
        </Button>
      </Toolbar>
    </AppBar>
  )
}

export default Navbar

