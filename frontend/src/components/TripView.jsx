import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Container,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Rating,
  Divider,
  IconButton
} from '@mui/material'
import {
  Map as MapIcon,
  Download as DownloadIcon,
  Edit as EditIcon,
  Star as StarIcon
} from '@mui/icons-material'
import axios from 'axios'
import { format } from 'date-fns'

const API_BASE = '/api'

function TripView() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [trip, setTrip] = useState(null)
  const [loading, setLoading] = useState(true)
  const [adjustDialogOpen, setAdjustDialogOpen] = useState(false)
  const [adjustRequirements, setAdjustRequirements] = useState('')

  useEffect(() => {
    fetchTrip()
  }, [id])

  const fetchTrip = async () => {
    try {
      const response = await axios.get(`${API_BASE}/trips/${id}`)
      setTrip(response.data)
    } catch (error) {
      console.error('获取行程失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (format) => {
    try {
      const response = await axios.post(
        `${API_BASE}/trips/${id}/export`,
        { format },
        { responseType: 'blob' }
      )
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${trip.city}_${trip.days}日游行程.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('导出失败:', error)
    }
  }

  const handleAdjust = async () => {
    try {
      await axios.put(`${API_BASE}/trips/${id}/adjust`, {
        requirements: adjustRequirements
      })
      setAdjustDialogOpen(false)
      setAdjustRequirements('')
      fetchTrip() // 刷新行程
    } catch (error) {
      console.error('调整失败:', error)
    }
  }

  if (loading) {
    return (
      <Container>
        <Typography>加载中...</Typography>
      </Container>
    )
  }

  if (!trip) {
    return (
      <Container>
        <Typography>行程不存在</Typography>
      </Container>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              {trip.city} {trip.days}日游行程
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <Chip label={trip.pace} size="small" />
              <Chip label={trip.transport_mode} size="small" />
              <Chip label={trip.priority} size="small" color="primary" />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<MapIcon />}
              onClick={() => navigate(`/trip/${id}/map`)}
            >
              查看地图
            </Button>
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={() => setAdjustDialogOpen(true)}
            >
              调整行程
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => handleExport('pdf')}
            >
              导出PDF
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => handleExport('ics')}
            >
              导出日历
            </Button>
          </Box>
        </Box>

        <Divider sx={{ my: 3 }} />

        {trip.days_plans?.map((dayPlan) => (
          <Card key={dayPlan.id} sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                第 {dayPlan.day_number} 天
              </Typography>
              {dayPlan.description && (
                <Typography variant="body2" color="text.secondary" paragraph>
                  {dayPlan.description}
                </Typography>
              )}

              <Grid container spacing={2} sx={{ mt: 2 }}>
                {dayPlan.activities?.map((activity) => (
                  <Grid item xs={12} md={6} key={activity.id}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="h6">{activity.name}</Typography>
                        <Chip label={activity.type} size="small" color="primary" />
                      </Box>
                      
                      {activity.rating && (
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <Rating value={activity.rating} readOnly size="small" />
                          <Typography variant="body2" sx={{ ml: 1 }}>
                            {activity.rating.toFixed(1)}
                          </Typography>
                        </Box>
                      )}

                      <Typography variant="body2" color="text.secondary" paragraph>
                        {activity.start_time} - {activity.end_time} 
                        {activity.duration_minutes && ` (${activity.duration_minutes}分钟)`}
                      </Typography>

                      {activity.address && (
                        <Typography variant="body2" color="text.secondary" paragraph>
                          📍 {activity.address}
                        </Typography>
                      )}

                      {activity.description && (
                        <Typography variant="body2" paragraph>
                          {activity.description}
                        </Typography>
                      )}

                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
                        {activity.tags?.map((tag, idx) => (
                          <Chip key={idx} label={tag} size="small" variant="outlined" />
                        ))}
                        {activity.price_range && (
                          <Chip 
                            label={`${activity.price_range} ${activity.price_estimate ? `¥${activity.price_estimate}` : ''}`}
                            size="small"
                            color="secondary"
                          />
                        )}
                      </Box>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        ))}
      </Paper>

      <Dialog open={adjustDialogOpen} onClose={() => setAdjustDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>调整行程</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="请描述您的调整需求"
            value={adjustRequirements}
            onChange={(e) => setAdjustRequirements(e.target.value)}
            placeholder="例如：希望增加更多美食体验，减少购物时间..."
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAdjustDialogOpen(false)}>取消</Button>
          <Button onClick={handleAdjust} variant="contained">确认调整</Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}

export default TripView

