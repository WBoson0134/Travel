import React, { useState } from 'react'
import {
  Container,
  Paper,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Box,
  Typography,
  Grid,
  Slider,
  CircularProgress,
  Alert
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const API_BASE = '/api'

function TripGenerator({ onTripGenerated }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const [formData, setFormData] = useState({
    city: '',
    days: 3,
    preferences: [],
    pace: '中庸',
    transport_mode: 'driving',
    priority: '效率优先'
  })

  const preferenceOptions = ['自然', '美食', '文化', '购物', '历史', '娱乐']
  const paceOptions = ['佛系', '中庸', '硬核']
  const transportOptions = [
    { value: 'driving', label: '自驾' },
    { value: 'walking', label: '步行' },
    { value: 'transit', label: '公共交通' },
    { value: 'bicycling', label: '骑行' }
  ]
  const priorityOptions = ['价格优先', '效率优先', '风景优先', '娱乐设施优先']

  const handlePreferenceToggle = (pref) => {
    setFormData(prev => ({
      ...prev,
      preferences: prev.preferences.includes(pref)
        ? prev.preferences.filter(p => p !== pref)
        : [...prev.preferences, pref]
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/trips/generate`, formData)
      const trip = response.data
      
      if (onTripGenerated) {
        onTripGenerated(trip)
      }
      
      navigate(`/trip/${trip.id}`)
    } catch (err) {
      setError(err.response?.data?.error || '生成行程失败，请重试')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          生成您的专属行程
        </Typography>
        
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="目的地城市"
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                required
                placeholder="例如：北京"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="出行天数"
                value={formData.days}
                onChange={(e) => setFormData({ ...formData, days: parseInt(e.target.value) || 1 })}
                inputProps={{ min: 1, max: 30 }}
                required
              />
            </Grid>

            <Grid item xs={12}>
              <Typography gutterBottom>兴趣偏好（可多选）</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {preferenceOptions.map(pref => (
                  <Chip
                    key={pref}
                    label={pref}
                    onClick={() => handlePreferenceToggle(pref)}
                    color={formData.preferences.includes(pref) ? 'primary' : 'default'}
                    variant={formData.preferences.includes(pref) ? 'filled' : 'outlined'}
                  />
                ))}
              </Box>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>出行节奏</InputLabel>
                <Select
                  value={formData.pace}
                  label="出行节奏"
                  onChange={(e) => setFormData({ ...formData, pace: e.target.value })}
                >
                  {paceOptions.map(pace => (
                    <MenuItem key={pace} value={pace}>{pace}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>交通方式</InputLabel>
                <Select
                  value={formData.transport_mode}
                  label="交通方式"
                  onChange={(e) => setFormData({ ...formData, transport_mode: e.target.value })}
                >
                  {transportOptions.map(opt => (
                    <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>优先级</InputLabel>
                <Select
                  value={formData.priority}
                  label="优先级"
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                >
                  {priorityOptions.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {error && (
              <Grid item xs={12}>
                <Alert severity="error">{error}</Alert>
              </Grid>
            )}

            <Grid item xs={12}>
              <Button
                type="submit"
                variant="contained"
                fullWidth
                size="large"
                disabled={loading || !formData.city}
                sx={{ py: 1.5 }}
              >
                {loading ? <CircularProgress size={24} /> : '生成行程'}
              </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Container>
  )
}

export default TripGenerator

