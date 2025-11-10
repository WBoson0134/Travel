import React, { useState, useEffect, useRef } from 'react'
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Chip,
  CircularProgress,
  IconButton,
  Divider
} from '@mui/material'
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Clear as ClearIcon
} from '@mui/icons-material'

const API_BASE = '/api'

function AIAssistant() {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const [userId] = useState(() => `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // 初始欢迎消息
  useEffect(() => {
    const welcomeMessage = {
      role: 'assistant',
      content: '您好！我是您的旅游助手，可以帮您规划行程、推荐景点、搜索酒店和航班等。有什么我可以帮助您的吗？',
      suggestions: ['规划行程', '推荐景点', '搜索酒店', '查询航班']
    }
    setMessages([welcomeMessage])
    setSuggestions(welcomeMessage.suggestions)
  }, [])

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 注意：新的FastAPI接口不包含对话历史功能
  // 对话历史现在由前端本地管理

  const handleSend = async (message = null) => {
    const messageToSend = message || inputMessage.trim()
    if (!messageToSend && !message) return

    // 添加用户消息
    const userMessage = {
      role: 'user',
      content: messageToSend
    }
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setLoading(true)
    setSuggestions([])

    try {
      // 构建消息历史（包含系统消息）
      const messageHistory = [
        { role: 'system', content: 'You are TripApp assistant. 你是一个专业的旅游助手，擅长回答关于旅游规划、景点推荐、行程安排等问题。' },
        ...messages.map(m => ({ role: m.role, content: m.content })),
        userMessage
      ]
      
      // 使用新的FastAPI接口
      // 默认使用 openai，如果没有配置则让后端自动选择
      const payload = {
        user_id: userId,
        message: messageToSend,
        context: {}
      }
      
      const response = await fetch(`${API_BASE}/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || data.detail || 'AI 助手请求失败')
      }

      // 添加AI回复
      const assistantMessage = {
        role: 'assistant',
        content: data.reply || data.answer || '抱歉，我无法理解您的问题。',
        suggestions: data.suggestions || []
      }
      setMessages(prev => [...prev, assistantMessage])
      setSuggestions(assistantMessage.suggestions)

    } catch (error) {
      console.error('发送消息失败:', error)
      const errorMessage = {
        role: 'assistant',
        content: `抱歉，发生了错误：${error.message}`,
        suggestions: ['重试', '清除对话']
      }
      setMessages(prev => [...prev, errorMessage])
      setSuggestions(errorMessage.suggestions)
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSuggestionClick = (suggestion) => {
    handleSend(suggestion)
  }

  const handleClearHistory = () => {
    // 清除本地对话历史
    const welcomeMessage = {
      role: 'assistant',
      content: '对话历史已清除。有什么我可以帮助您的吗？',
      suggestions: ['规划行程', '推荐景点', '搜索酒店', '查询航班']
    }
    setMessages([welcomeMessage])
    setSuggestions(welcomeMessage.suggestions)
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ height: '80vh', display: 'flex', flexDirection: 'column' }}>
        {/* 头部 */}
        <Box
          sx={{
            p: 2,
            borderBottom: 1,
            borderColor: 'divider',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            bgcolor: 'primary.main',
            color: 'primary.contrastText'
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BotIcon />
            <Typography variant="h6">AI 旅游助手</Typography>
          </Box>
          <IconButton
            size="small"
            onClick={handleClearHistory}
            sx={{ color: 'inherit' }}
            title="清除对话历史"
          >
            <ClearIcon />
          </IconButton>
        </Box>

        {/* 消息列表 */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 2,
            bgcolor: 'grey.50'
          }}
        >
          <List>
            {messages.map((message, index) => (
              <React.Fragment key={index}>
                <ListItem
                  sx={{
                    justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                    alignItems: 'flex-start',
                    mb: 1
                  }}
                >
                  {message.role === 'assistant' && (
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        <BotIcon />
                      </Avatar>
                    </ListItemAvatar>
                  )}
                  <Paper
                    elevation={1}
                    sx={{
                      p: 2,
                      maxWidth: '70%',
                      bgcolor: message.role === 'user' ? 'primary.light' : 'white',
                      color: message.role === 'user' ? 'primary.contrastText' : 'text.primary'
                    }}
                  >
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {message.content}
                    </Typography>
                  </Paper>
                  {message.role === 'user' && (
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'secondary.main' }}>
                        <PersonIcon />
                      </Avatar>
                    </ListItemAvatar>
                  )}
                </ListItem>
                {index < messages.length - 1 && <Divider component="li" />}
              </React.Fragment>
            ))}
            {loading && (
              <ListItem>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    <BotIcon />
                  </Avatar>
                </ListItemAvatar>
                <CircularProgress size={20} />
              </ListItem>
            )}
            <div ref={messagesEndRef} />
          </List>
        </Box>

        {/* 建议按钮 */}
        {suggestions.length > 0 && (
          <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', bgcolor: 'white' }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              快速操作：
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {suggestions.map((suggestion, index) => (
                <Chip
                  key={index}
                  label={suggestion}
                  onClick={() => handleSuggestionClick(suggestion)}
                  size="small"
                  clickable
                  color="primary"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        )}

        {/* 输入框 */}
        <Box
          sx={{
            p: 2,
            borderTop: 1,
            borderColor: 'divider',
            bgcolor: 'white',
            display: 'flex',
            gap: 1
          }}
        >
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="输入您的问题..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
            inputRef={inputRef}
            variant="outlined"
            size="small"
          />
          <Button
            variant="contained"
            color="primary"
            onClick={() => handleSend()}
            disabled={loading || !inputMessage.trim()}
            startIcon={<SendIcon />}
            sx={{ minWidth: 100 }}
          >
            发送
          </Button>
        </Box>
      </Paper>
    </Container>
  )
}

export default AIAssistant

