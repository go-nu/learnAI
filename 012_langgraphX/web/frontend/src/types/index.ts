export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  type: 'text' | 'image'
  created_at: string
}

export interface ImageItem {
  filename: string
  url: string
  created_at: number
}

export type TabType = 'chat' | 'image'
