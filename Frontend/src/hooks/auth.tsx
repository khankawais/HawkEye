import { useRouter } from "next/router"
import { useEffect, useMemo } from "react"

import { useSnackbar } from "notistack"
import Logout from "@mui/icons-material/Logout"
import Settings from "@mui/icons-material/Settings"
import HomeOutlinedIcon from "@mui/icons-material/HomeOutlined"
import AnalyticsOutlinedIcon from "@mui/icons-material/AnalyticsOutlined"
import FilterCenterFocusOutlinedIcon from "@mui/icons-material/FilterCenterFocusOutlined"

import { useApi } from "@hooks/useApi"
import { ENDPOINTS } from "@utils/constants"
import { NavLink, MenuLink } from "@utils/types"
import { getBrowserItem } from "@utils/browser-utility"
import { AuthTypes, useAppContext } from "@contexts/index"

export const useRouteLinks = () => {
  const router = useRouter()
  const { dispatch } = useAppContext()

  const NavLinks: NavLink[] = useMemo(
    () => [
      {
        type: "group",
        label: "App",
        children: [
          {
            type: "item",
            label: "Dashboard",
            href: "/app",
            icon: <AnalyticsOutlinedIcon fontSize="small" color="primary" />,
            exact: true,
          },
          {
            type: "item",
            label: "Alerts",
            href: "/app/alerts",
            icon: (
              <FilterCenterFocusOutlinedIcon fontSize="small" color="error" />
            ),
          },
        ],
      },
    ],
    []
  )

  const MenuLinks: MenuLink[] = useMemo(
    () => [
      {
        type: "item",
        href: "/app",
        label: "Home",
        icon: <HomeOutlinedIcon fontSize="small" />,
      },
      {
        type: "item",
        label: "Settings",
        href: "/app/settings",
        icon: <Settings fontSize="small" />,
      },
      {
        type: "item",
        color: "error",
        label: "Logout",
        icon: <Logout fontSize="small" />,
        onClick: () => {
          dispatch({ type: AuthTypes.LOGOUT })
          router.push("/")
        },
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [router, dispatch]
  )

  useEffect(() => {
    let app = router.asPath.split("/app/")[1]

    if (router.asPath.split("/app/")[1]) {
      app = app.split("/")[0]
    }

    // eslint-disable-next-line
  }, [router.asPath])

  return { NavLinks, MenuLinks }
}

export const AuthWrapper = ({ children }: { children: any }) => {
  const router = useRouter()

  const {} = useAlerts()
  const { dispatch } = useAppContext()

  const checkAuth = async () => {
    try {
      let route = "/"

      const token = getBrowserItem()

      if (!token) {
        if (router.asPath.startsWith("/app")) route = "/"
        else route = router.asPath

        dispatch({ type: AuthTypes.LOGOUT })
        router.replace(route)
        return
      }

      if (router.asPath.startsWith("/app")) {
        route = router.asPath
      } else if (
        router.asPath.startsWith("/auth/login") ||
        router.asPath.startsWith("/auth/register")
      ) {
        route = "/"
      } else if (router.asPath.startsWith("/auth")) {
        route = router.asPath
      } else {
        route = "/"
      }

      router.prefetch(route)
      router.replace(route)
    } catch (error: any) {}
  }

  useEffect(() => {
    checkAuth()
    // eslint-disable-next-line
  }, [])

  return children
}

let interval: any = null

export const useAlerts = () => {
  const [api] = useApi()
  const { enqueueSnackbar } = useSnackbar()

  useEffect(() => {
    fetchAlerts()

    interval = setInterval(fetchAlerts, 60000)

    return () => {
      clearInterval(interval)
    }

    // eslint-disable-next-line
  }, [])

  const updateStatus = async (id: string, status: string) => {
    try {
      await api({
        method: "PUT",
        uri: `${ENDPOINTS.clients}/changealertstatus?id=${id}&status=${status}`,
      })
    } catch (error: any) {}
  }

  const fetchAlerts = async () => {
    try {
      const response = await api({
        method: "GET",
        uri: `${ENDPOINTS.clients}/getalerts?status=new&type=normal`,
      })

      if (Array.isArray(response)) {
        response.map((alert: any) => {
          enqueueSnackbar(`${alert.host_name || ""}: ${alert.alert_type}`, {
            variant: "warning",
            autoHideDuration: 3000,
          })
          updateStatus(alert.id, "read")
        })
      }
    } catch (err) {}
  }

  return { fetchAlerts }
}
