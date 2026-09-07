import { NextResponse, type NextRequest } from "next/server"
import { getToken } from "next-auth/jwt"

const ADMIN_ONLY_ROUTES = [/^\/users(\/|$)/]
const AUTHENTICATED_ROUTES = [/^\/dashboard(\/|$)/, /^\/settings(\/|$)/, /^\/rma(\/|$)/]

export async function middleware(req: NextRequest) {
  const pathname = req.nextUrl.pathname

  const isAdminRoute = ADMIN_ONLY_ROUTES.some((re) => re.test(pathname))
  const isProtected =
    isAdminRoute || AUTHENTICATED_ROUTES.some((re) => re.test(pathname))

  if (!isProtected) return NextResponse.next()

  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET })

  if (!token) {
    const loginUrl = new URL("/login", req.url)
    loginUrl.searchParams.set("callbackUrl", pathname)
    return NextResponse.redirect(loginUrl)
  }

  if (isAdminRoute && token.role !== "ADMIN") {
    const deniedUrl = new URL("/dashboard", req.url)
    deniedUrl.searchParams.set("denied", "1")
    return NextResponse.redirect(deniedUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/dashboard/:path*", "/settings/:path*", "/rma/:path*", "/users/:path*"],
}
