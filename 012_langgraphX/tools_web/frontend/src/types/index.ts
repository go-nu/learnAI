export type Mode = 'text2img' | 'img2img'

export interface GenerateResult {
  status: string
  message: string
  image_url: string | null
  record_id: number
}

export interface ImageItem {
  filename: string
  url: string
  created_at: number
  prompt: string
  mode: Mode
}
