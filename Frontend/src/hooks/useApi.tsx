import { useSnackbar } from "notistack"
import { useLayoutEffect, useEffect, useRef } from "react"

import DateUtility from "@utils/date"
import { BASE_URL } from "@utils/constants"
import { Response, T } from "@utils/types"
import { getBrowserItem } from "@utils/browser-utility"

const useBrowserLayoutEffect =
  typeof window !== "undefined" ? useLayoutEffect : useEffect

export const useApi = () => {
  const { enqueueSnackbar } = useSnackbar()

  let controller: any = null

  const isMounted = useRef(false)
  useBrowserLayoutEffect((): (() => void) => {
    controller = new AbortController()

    isMounted.current = true
    return (): void => {
      isMounted.current = false
      controller.abort()
    }
  }, [])

  const api = async ({
    uri,
    body,
    message,
    method = "GET",
    contentType = "application/json",
  }: {
    body?: any
    uri: string
    method?: string
    message?: string
    contentType?: string
  }): Promise<T> => {
    try {
      const headers = new Headers()
      headers.append("Content-Type", contentType)

      const token = getBrowserItem()
      if (token) {
        headers.append("Authorization", `Basic ${window.btoa(token)}`)
      }

      const response = await fetch(BASE_URL + uri, {
        body,
        method,
        headers,
        signal: controller?.signal,
      })

      if (!response.ok) throw response

      const data: Response = await response.json()

      if (process && process.env.NODE_ENV === "development") {
        console.log(`[Response at ${DateUtility.getLocaleDate()}]:`, data)
      }

      if (message) {
        enqueueSnackbar(message, {
          variant: "success",
          autoHideDuration: 3000,
        })
      }

      if (isMounted.current) {
        // can be used to set local state if needed
        return data
      }
    } catch (err: any) {
      // need to assign to a variable to prevent error when we do error.json() below
      let error = err

      if (!isErrorWithMessage(err)) {
        error = await error.json()
        error = {
          message: error.detail || error.message,
          status: err.status,
        }
      } else {
        error = {
          message: err.message,
          status: error.status || 500,
        }
      }

      if (process && process.env.NODE_ENV === "development") {
        console.log(`[Error at ${DateUtility.getLocaleDate()}]:`, error)
        body && console.log(`Error for Body`, JSON.parse(body))
      }

      let status = error.status

      if (status) {
        if (
          !Array.isArray(error.message) &&
          error.message !== "The user aborted a request."
        ) {
          enqueueSnackbar(error?.message, {
            variant: "error",
            autoHideDuration: 3000,
          })
        }

        throw error
      } else {
        throw error
      }
    }
  }

  return [api]
}

type ErrorWithMessage = {
  message: string
  status?: number
}

function isErrorWithMessage(error: unknown): error is ErrorWithMessage {
  return (
    typeof error === "object" &&
    error !== null &&
    "message" in error &&
    typeof (error as Record<string, unknown>).message === "string"
  )
}
