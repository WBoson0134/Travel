import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
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
  IconButton,
  CircularProgress,
  Alert
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
  const location = useLocation()
  const [trip, setTrip] = useState(null)
  const [loading, setLoading] = useState(true)
  const [adjustDialogOpen, setAdjustDialogOpen] = useState(false)
  const [adjustRequirements, setAdjustRequirements] = useState('')
  const [parsedTrip, setParsedTrip] = useState(null)

  useEffect(() => {
    // 如果从 location state 中获取了 trip 数据，直接使用
    if (location.state?.trip) {
      const tripData = location.state.trip
      const parsed = parseAITripResponse(tripData)
      setParsedTrip(parsed)
      setTrip(parsed)
      // 在控制台打印解析后的行程 JSON
      console.log('解析后的行程 (JSON):', JSON.stringify(parsed, null, 2))
      console.log('解析后的行程 (对象):', parsed)
      setLoading(false)
    } else if (id) {
      // 否则从 API 获取
      fetchTrip()
    } else {
      // 如果没有 id 也没有 state，显示生成中
      setLoading(false)
    }
  }, [id, location.state])

  // 解析 AI 返回的 trip 数据
  const parseAITripResponse = (aiResponse) => {
    try {
      // 如果已经是解析好的格式，直接返回
      if (aiResponse.days && Array.isArray(aiResponse.days)) {
        return {
          city: aiResponse.city || '未知城市',
          days: aiResponse.days?.length || 0,
          pace: aiResponse.pace || '中庸',
          transport: aiResponse.transport || 'driving',
          priority: aiResponse.priority || '效率优先',
          days_plans: aiResponse.days.map((day, index) => ({
            id: index + 1,
            day_number: day.day_number || index + 1,
            description: day.description || `第${index + 1}天的行程`,
            activities: (day.activities || []).map((act, actIndex) => ({
              id: `${index + 1}-${actIndex + 1}`,
              name: act.name || '未命名活动',
              type: act.type || '其他',
              address: act.address || '',
              start_time: act.start_time || '09:00',
              end_time: act.end_time || '12:00',
              duration_minutes: act.duration_minutes || 180,
              description: act.description || '',
              rating: act.rating || 4.5,
              tags: act.tags || [],
              price_range: act.price_range || '$$',
              price_estimate: act.price_estimate || 50,
              order: act.order || actIndex + 1
            }))
          }))
        }
      }

      // 如果是阿里云百炼的响应格式
      if (aiResponse.output?.choices?.[0]?.message?.content) {
        const content = aiResponse.output.choices[0].message.content
        // 尝试提取 JSON
        let jsonStr = content
        if (content.includes('```json')) {
          jsonStr = content.split('```json')[1].split('```')[0].trim()
        } else if (content.includes('```')) {
          jsonStr = content.split('```')[1].split('```')[0].trim()
        }
        
        const parsed = JSON.parse(jsonStr)
        return parseAITripResponse(parsed) // 递归解析
      }

      // 如果直接是字符串，尝试解析
      if (typeof aiResponse === 'string') {
        const parsed = JSON.parse(aiResponse)
        return parseAITripResponse(parsed)
      }

      return null
    } catch (error) {
      console.error('解析 AI 响应失败:', error)
      return null
    }
  }

  const fetchTrip = async () => {
    try {
      const response = await axios.get(`${API_BASE}/trips/${id}`)
      setTrip(response.data)
      setParsedTrip(response.data)
    } catch (error) {
      console.error('获取行程失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (format) => {
    try {
      // 如果有 id，使用 API 导出
      if (id) {
        const response = await axios.post(
          `${API_BASE}/trips/${id}/export`,
          { format },
          { responseType: 'blob' }
        )
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        const displayTrip = parsedTrip || trip
        link.setAttribute('download', `${displayTrip.city}_${displayTrip.days}日游行程.${format}`)
        document.body.appendChild(link)
        link.click()
        link.remove()
      } else {
        // 如果没有 id，使用当前 trip 数据导出
        // 这里可以调用一个客户端导出函数，或者发送到后端处理
        const displayTrip = parsedTrip || trip
        const exportData = {
          city: displayTrip?.city || '未知城市',
          days: displayTrip?.days || 0,
          days_plans: displayTrip?.days_plans || []
        }
        
        if (format === 'ics') {
          // 简单的 ICS 导出（客户端）
          const icsContent = generateICS(exportData)
          const blob = new Blob([icsContent], { type: 'text/calendar' })
          const url = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.setAttribute('download', `${exportData.city}_${exportData.days}日游行程.ics`)
          document.body.appendChild(link)
          link.click()
          link.remove()
        } else {
          alert('PDF 导出需要保存行程后才能使用')
        }
      }
    } catch (error) {
      console.error('导出失败:', error)
      alert('导出失败，请重试')
    }
  }

  // 生成 ICS 文件内容
  const generateICS = (tripData) => {
    const now = new Date()
    const startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    
    let ics = 'BEGIN:VCALENDAR\n'
    ics += 'VERSION:2.0\n'
    ics += 'PRODID:-//Travel Planner//EN\n'
    ics += 'CALSCALE:GREGORIAN\n'
    
    tripData.days_plans?.forEach((dayPlan) => {
      dayPlan.activities?.forEach((activity) => {
        const activityDate = new Date(startDate)
        activityDate.setDate(startDate.getDate() + dayPlan.day_number - 1)
        
        const [startHour, startMin] = activity.start_time.split(':').map(Number)
        const [endHour, endMin] = activity.end_time.split(':').map(Number)
        
        const startDateTime = new Date(activityDate)
        startDateTime.setHours(startHour, startMin, 0)
        
        const endDateTime = new Date(activityDate)
        endDateTime.setHours(endHour, endMin, 0)
        
        const formatDate = (date) => {
          return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
        }
        
        ics += 'BEGIN:VEVENT\n'
        ics += `DTSTART:${formatDate(startDateTime)}\n`
        ics += `DTEND:${formatDate(endDateTime)}\n`
        ics += `SUMMARY:${activity.name}\n`
        ics += `DESCRIPTION:${activity.description || ''}\n`
        if (activity.address) {
          ics += `LOCATION:${activity.address}\n`
        }
        ics += 'END:VEVENT\n'
      })
    })
    
    ics += 'END:VCALENDAR\n'
    return ics
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
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, textAlign: 'center' }}>
        <CircularProgress sx={{ mb: 2 }} />
        <Typography variant="h6">加载中...</Typography>
      </Container>
    )
  }

  // 如果 trip 是空的，显示生成中提示
  if (!trip || !parsedTrip) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, textAlign: 'center' }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <CircularProgress sx={{ mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            生成中，请稍候…
          </Typography>
          <Typography variant="body1" color="text.secondary">
            正在为您生成专属旅行计划
          </Typography>
        </Paper>
      </Container>
    )
  }

  // 使用解析后的 trip 数据
  const displayTrip = parsedTrip || trip

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              {displayTrip.city} {displayTrip.days}日游行程
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
              <Chip label={displayTrip.pace || '中庸'} size="small" />
              <Chip label={displayTrip.transport || displayTrip.transport_mode || 'driving'} size="small" />
              <Chip label={displayTrip.priority || '效率优先'} size="small" color="primary" />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {id && (
              <>
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
              </>
            )}
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

        {/* 每日卡片展示 */}
        {displayTrip.days_plans && displayTrip.days_plans.length > 0 ? (
          displayTrip.days_plans.map((dayPlan) => (
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
          ))
        ) : (
          <Alert severity="info" sx={{ mt: 2 }}>
            暂无行程数据
          </Alert>
        )}
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

