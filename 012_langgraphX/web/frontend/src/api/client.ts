import axios from 'axios'
import type { ChatMessage, ImageItem } from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 300000, // 5분 (이미지 생성 대기)
})

export const generateResponse = async (prompt: string) => {
  const { data } = await api.post('/generate/', { prompt })
  return data as { response: string; type: 'text' | 'image' }
}

export const fetchHistory = async () => {
  const { data } = await api.get('/history/')
  return data.messages as ChatMessage[]
}

export const clearHistory = async () => {
  await api.delete('/history/')
}

export const fetchImages = async () => {
  const { data } = await api.get('/images/')
  return data.images as ImageItem[]
}
