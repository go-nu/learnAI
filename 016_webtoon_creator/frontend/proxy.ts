import { NextRequest, NextResponse } from 'next/server';

// /dashboard 하위 경로 보호: sessionid 쿠키가 없으면 /login 으로 리다이렉트
export default function proxy(request: NextRequest) {
  const sessionId = request.cookies.get('sessionid')?.value;

  if (!sessionId) {
    const loginUrl = new URL('/login', request.url);
    // 로그인 성공 후 돌아올 경로 전달
    loginUrl.searchParams.set('next', request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*'],
};
