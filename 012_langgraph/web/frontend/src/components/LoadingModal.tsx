import { useEffect } from 'react'
import Swal from 'sweetalert2'

interface LoadingModalProps {
  isLoading: boolean
  message?: string
}

export function LoadingModal({ isLoading, message = '처리 중입니다...' }: LoadingModalProps) {
  useEffect(() => {
    if (isLoading) {
      Swal.fire({
        title: message,
        html: '<span style="color:#767676;font-size:14px">잠시만 기다려주세요.</span>',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading()
        },
      })
    } else {
      if (Swal.isVisible()) {
        Swal.close()
      }
    }
  }, [isLoading, message])

  return null
}
