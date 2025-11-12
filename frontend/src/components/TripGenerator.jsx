import React, { useEffect, useRef, useState } from 'react'
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
  CircularProgress,
  Alert,
  Backdrop,
  LinearProgress
} from '@mui/material'
import { useNavigate } from 'react-router-dom'

function TripGenerator({ onTripGenerated }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const [formData, setFormData] = useState({
    city: '',
    days: 3,
    preferences: [],
    pace: '中庸',
    transport: 'driving',
    priority: '效率优先'
  })
  
  const [trip, setTrip] = useState(null)
  const [showProgress, setShowProgress] = useState(false)
  const [progress, setProgress] = useState(0)
  const progressTimerRef = useRef(null)

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
    setTrip(null)
    startProgress()

    const { city, days, preferences, pace, transport, priority } = formData
    try {
      const res = await fetch('/api/generate_trip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city, days, preferences, pace, transport, priority })
      })

      const rawText = await res.text()

      if (!rawText) {
        throw new Error('服务器没有返回任何数据')
      }

      let data
      try {
        data = JSON.parse(rawText)
      } catch (parseErr) {
        console.error('解析生成行程响应失败:', parseErr, rawText)
        throw new Error('响应格式异常，请稍后重试')
      }

      if (!res.ok || data.error) {
        throw new Error(data.error || '生成行程失败，请重试')
      }

      const tripData = buildTripData(data)
      persistAndNavigate(tripData)
    } catch (err) {
      const errorMessage = err.message || '生成行程失败，请重试'
      console.error('生成行程错误:', err)
      setError(errorMessage)
      alert(`错误: ${errorMessage}`)
      failProgress()
    } finally {
      setLoading(false)
    }
  }

  const buildTripData = (rawData, extra = {}) => {
    const merged = {
      ...rawData,
      city: rawData.city || formData.city,
      pace: rawData.pace || formData.pace,
      transport: rawData.transport || formData.transport,
      priority: rawData.priority || formData.priority,
      preferences: rawData.preferences || formData.preferences,
      requested_days: formData.days,
      ...extra
    }

    if (Array.isArray(rawData.days)) {
      merged.days = rawData.days
    }

    return merged
  }

  const persistAndNavigate = (tripData, options = {}) => {
    setTrip(tripData)
    console.log('生成的行程 (JSON):', JSON.stringify(tripData, null, 2))
    console.log('生成的行程 (对象):', tripData)
    finishProgress()

    if (onTripGenerated) {
      onTripGenerated(tripData)
    }

    try {
      sessionStorage.setItem('latestTripPlan', JSON.stringify(tripData))
    } catch (err) {
      console.warn('无法写入 sessionStorage:', err)
    }

    if (options.notice) {
      alert(options.notice)
    }

    navigate('/trip-result', { state: { trip: tripData } })
  }

  const startProgress = () => {
    setShowProgress(true)
    setProgress(5)
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current)
    }
    progressTimerRef.current = setInterval(() => {
      setProgress(prev => {
        if (prev >= 95) return prev
        const increment = Math.random() * 10 + 3
        return Math.min(prev + increment, 95)
      })
    }, 700)
  }

  const finishProgress = () => {
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current)
      progressTimerRef.current = null
    }
    setProgress(100)
    setTimeout(() => {
      setShowProgress(false)
      setProgress(0)
    }, 500)
  }

  const failProgress = () => {
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current)
      progressTimerRef.current = null
    }
    setShowProgress(false)
    setProgress(0)
  }

  useEffect(() => {
    return () => {
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current)
      }
    }
  }, [])


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
                  value={formData.transport}
                  label="交通方式"
                  onChange={(e) => setFormData({ ...formData, transport: e.target.value })}
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
        
        {/* 显示生成的行程结果 */}
        {trip && (
          <Box sx={{ mt: 4 }}>
            <Paper elevation={2} sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                生成的行程结果
              </Typography>
              <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="body2" component="pre" sx={{ 
                  whiteSpace: 'pre-wrap', 
                  wordBreak: 'break-word',
                  fontFamily: 'monospace',
                  fontSize: '0.875rem'
                }}>
                  {JSON.stringify(trip, null, 2)}
                </Typography>
              </Box>
            </Paper>
          </Box>
        )}
      </Paper>

      <Backdrop
        open={showProgress}
        sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
      >
        <Box sx={{ width: 320, p: 4, bgcolor: 'rgba(0,0,0,0.7)', borderRadius: 2, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            AI 正在生成行程…
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            这可能需要一些时间，请耐心等待。
          </Typography>
          <LinearProgress variant="determinate" value={progress} sx={{ height: 8, borderRadius: 4 }} />
        </Box>
      </Backdrop>
    </Container>
  )
}

export default TripGenerator

