import axios from 'axios'
import type { GenerateResult, ImageItem } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000,
})

export const generateText2Img = async (prompt: string): Promise<GenerateResult> => {
  const { data } = await api.post('/text2img/', { prompt }, {
    headers: { 'Content-Type': 'application/json' },
  })
  return data
}

export const generateImg2Img = async (
  prompt: string,
  image: File,
  denoise: number,
): Promise<GenerateResult> => {
  const form = new FormData()
  form.append('prompt', prompt)
  form.append('image', image)
  form.append('denoise', String(denoise))
  const { data } = await api.post('/img2img/', form)
  return data
}

export const fetchImages = async (): Promise<ImageItem[]> => {
  const { data } = await api.get('/images/')
  return data.images as ImageItem[]
}

export const clearImages = async (): Promise<void> => {
  await api.delete('/images/')
}
