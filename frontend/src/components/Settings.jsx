import React, { useState, useEffect } from 'react'
import {
  Container,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material'
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon,
  SmartToy as BotIcon,
  Hotel as HotelIcon,
  Flight as FlightIcon,
  Map as MapIcon,
  Info as InfoIcon
} from '@mui/icons-material'

const API_BASE = '/api'

function Settings() {
  const [configStatus, setConfigStatus] = useState(null)
  const [aiProviders, setAiProviders] = useState(null) // 新增：存储AI提供商数据
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadConfigStatus()
  }, [])

  const loadConfigStatus = async () => {
    try {
      setLoading(true)
      // 使用新的FastAPI端点
      const response = await fetch(`${API_BASE}/ai/providers`)
      if (!response.ok) {
        throw new Error('获取配置状态失败')
      }
      const data = await response.json()
      
      // 保存原始数据
      setAiProviders(data)
      
      // 转换为原有格式以保持兼容
      const formattedData = {
        ai: {
          openai: {
            configured: data.providers.find(p => p.name === 'openai' || p.name === 'aliyun')?.configured || false,
            base_url: null
          },
          dify: {
            configured: data.providers.find(p => p.name === 'dify')?.configured || false,
            base_url: null
          }
        },
        travel_apis: {},
        maps: {}
      }
      
      setConfigStatus(formattedData)
    } catch (err) {
      setError(err.message)
      console.error('加载配置状态失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const StatusChip = ({ configured }) => (
    <Chip
      icon={configured ? <CheckCircleIcon /> : <CancelIcon />}
      label={configured ? '已配置' : '未配置'}
      color={configured ? 'success' : 'error'}
      size="small"
    />
  )

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ mt: 4, mb: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ mt: 2 }}>
          加载配置状态中...
        </Typography>
      </Container>
    )
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    )
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, gap: 1 }}>
          <SettingsIcon color="primary" />
          <Typography variant="h4" component="h1">
            AI配置设置
          </Typography>
        </Box>

        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>注意：</strong>API密钥需要在服务器端的 <code>.env</code> 文件中配置。
            此页面仅显示当前配置状态，不显示实际的密钥值。
          </Typography>
        </Alert>

        {/* AI服务配置 */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
              <BotIcon color="primary" />
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                AI服务配置
              </Typography>
              <StatusChip 
                configured={aiProviders?.providers?.some(p => p.configured) || false} 
              />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              {aiProviders?.providers?.map((provider) => (
                <Grid item xs={12} md={6} key={provider.name}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="h6" sx={{ textTransform: 'capitalize' }}>
                          {provider.name === 'aliyun' ? '阿里云百炼' : 
                           provider.name === 'openai' ? 'OpenAI' :
                           provider.name === 'openrouter' ? 'OpenRouter' :
                           provider.name === 'ollama' ? 'Ollama' :
                           provider.name === 'dify' ? 'Dify' : provider.name}
                        </Typography>
                        <StatusChip configured={provider.configured} />
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {provider.name === 'aliyun' ? '用于AI助手对话和行程生成' :
                         provider.name === 'dify' ? '可选的AI服务提供商' :
                         'OpenAI兼容接口'}
                      </Typography>
                      {provider.name === aiProviders?.primary && (
                        <Chip label="默认" size="small" color="primary" sx={{ mt: 1 }} />
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* 外部旅游API配置 */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
              <HotelIcon color="primary" />
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                外部旅游API配置
              </Typography>
              <StatusChip 
                configured={
                  configStatus?.travel_apis?.booking?.configured ||
                  configStatus?.travel_apis?.amadeus?.configured ||
                  configStatus?.travel_apis?.tripadvisor?.configured
                } 
              />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle1">Booking.com</Typography>
                      <StatusChip configured={configStatus?.travel_apis?.booking?.configured} />
                    </Box>
                    <Typography variant="body2">
                      酒店搜索
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle1">Amadeus</Typography>
                      <StatusChip configured={configStatus?.travel_apis?.amadeus?.configured} />
                    </Box>
                    <Typography variant="body2">
                      酒店和航班搜索
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle1">TripAdvisor</Typography>
                      <StatusChip configured={configStatus?.travel_apis?.tripadvisor?.configured} />
                    </Box>
                    <Typography variant="body2">
                      景点搜索
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* 地图API配置 */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
              <MapIcon color="primary" />
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                地图API配置
              </Typography>
              <StatusChip configured={configStatus?.maps?.google_maps?.configured} />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle1">Google Maps</Typography>
                  <StatusChip configured={configStatus?.maps?.google_maps?.configured} />
                </Box>
                <Typography variant="body2">
                  用于地图显示和路线规划
                </Typography>
              </CardContent>
            </Card>
          </AccordionDetails>
        </Accordion>

        {/* 配置指南 */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <InfoIcon color="primary" />
              <Typography variant="h6">配置指南</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="h6" gutterBottom>
              如何配置AI服务
            </Typography>
            <List>
              <ListItem>
                <ListItemIcon>
                  <InfoIcon />
                </ListItemIcon>
                <ListItemText
                  primary="1. 创建 .env 文件"
                  secondary="在项目根目录创建 .env 文件（如果还没有）"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <InfoIcon />
                </ListItemIcon>
                <ListItemText
                  primary="2. 添加AI配置"
                  secondary={
                    <Box component="pre" sx={{ mt: 1, fontSize: '0.875rem' }}>
{`# 阿里云百炼配置
OPENAI_API_KEY=your_dashscope_api_key
OPENAI_BASE_URL=https://dashscope.aliyun.com/api/v1

# 或使用Dify
DIFY_API_KEY=your_dify_api_key
DIFY_API_BASE=https://api.dify.ai/v1`}
                    </Box>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <InfoIcon />
                </ListItemIcon>
                <ListItemText
                  primary="3. 重启后端服务"
                  secondary="修改配置后需要重启后端服务才能生效"
                />
              </ListItem>
            </List>
            <Divider sx={{ my: 2 }} />
            <Typography variant="body2" color="text.secondary">
              详细配置说明请参考 <code>API_INTEGRATION.md</code> 文件
            </Typography>
          </AccordionDetails>
        </Accordion>

        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            最后更新: {new Date().toLocaleString()}
          </Typography>
        </Box>
      </Paper>
    </Container>
  )
}

export default Settings

