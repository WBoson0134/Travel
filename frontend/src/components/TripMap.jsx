import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import { Container, Paper, Typography, Box, Button, CircularProgress } from '@mui/material'
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material'
import axios from 'axios'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// 修复默认图标问题
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const API_BASE = '/api'

function TripMap() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [mapData, setMapData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMapData()
  }, [id])

  const fetchMapData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/trips/${id}/map`)
      setMapData(response.data)
    } catch (error) {
      console.error('获取地图数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Container>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <CircularProgress />
        </Box>
      </Container>
    )
  }

  if (!mapData || !mapData.activities || mapData.activities.length === 0) {
    return (
      <Container>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography>暂无地图数据</Typography>
          <Button onClick={() => navigate(`/trip/${id}`)} sx={{ mt: 2 }}>
            返回行程详情
          </Button>
        </Paper>
      </Container>
    )
  }

  // 计算中心点
  const centerLat = mapData.activities.reduce((sum, a) => sum + a.latitude, 0) / mapData.activities.length
  const centerLng = mapData.activities.reduce((sum, a) => sum + a.longitude, 0) / mapData.activities.length

  // 按天分组活动
  const activitiesByDay = {}
  mapData.activities.forEach(activity => {
    if (!activitiesByDay[activity.day]) {
      activitiesByDay[activity.day] = []
    }
    activitiesByDay[activity.day].push(activity)
  })

  // 按天分组路线
  const routesByDay = {}
  mapData.routes?.forEach(route => {
    const fromDay = mapData.activities.find(a => a.id === route.from.id)?.day
    if (fromDay) {
      if (!routesByDay[fromDay]) {
        routesByDay[fromDay] = []
      }
      routesByDay[fromDay].push(route)
    }
  })

  const colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h5">{mapData.city} 行程地图</Typography>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(`/trip/${id}`)}
          >
            返回
          </Button>
        </Box>
      </Paper>

      <Paper elevation={3} sx={{ height: '600px', overflow: 'hidden' }}>
        <MapContainer
          center={[centerLat, centerLng]}
          zoom={12}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* 绘制路线 */}
          {Object.keys(routesByDay).map((day, dayIdx) => {
            const dayRoutes = routesByDay[day]
            return dayRoutes.map((route, routeIdx) => {
              const positions = [
                [route.from.lat, route.from.lng],
                [route.to.lat, route.to.lng]
              ]
              return (
                <Polyline
                  key={`route-${day}-${routeIdx}`}
                  positions={positions}
                  color={colors[dayIdx % colors.length]}
                  weight={3}
                  opacity={0.7}
                />
              )
            })
          })}

          {/* 绘制标记点 */}
          {mapData.activities.map((activity, idx) => (
            <Marker
              key={activity.id}
              position={[activity.latitude, activity.longitude]}
            >
              <Popup>
                <Box>
                  <Typography variant="subtitle1" fontWeight="bold">
                    {activity.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    第{activity.day}天 - 第{activity.order}站
                  </Typography>
                  <Typography variant="body2">
                    类型: {activity.type}
                  </Typography>
                </Box>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </Paper>
    </Container>
  )
}

export default TripMap

