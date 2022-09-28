import { useState, useEffect } from "react"

import { Box } from "@mui/material"
import { Grid } from "@mui/material"
import { TextField } from "@mui/material"
import { Edit } from "@mui/icons-material"
import { Delete } from "@mui/icons-material"
import { CircularProgress } from "@mui/material"

import { useApi } from "@hooks/useApi"
import { Alert } from "@components/Alert"
import { toTitleCase } from "@utils/common"
import { Select } from "@components/Select"
import { Button } from "@components/Button"
import { ENDPOINTS } from "@utils/constants"
import { IconButton } from "@components/IconButton"

export function EditStatus({
  value,
  onSubmit,
}: {
  value: any
  onSubmit?: (args: any) => void
}) {
  const [api] = useApi()

  const [loading, setLoading] = useState<boolean>(false)

  const handleSubmit = async (status: string) => {
    try {
      setLoading(true)

      await api({
        method: "PUT",
        uri: `${ENDPOINTS.clients}/changealertstatus?id=${value.id}&status=${status}`,
        message: "Status updated successfully",
      })

      if (onSubmit) onSubmit({ ...value, status })
    } catch (error: any) {
    } finally {
      setLoading(false)
    }
  }

  return (
    <Select
      fullWidth
      size="small"
      label="Status"
      value={value?.status}
      disabled={loading || value.status === "resolved"}
      onChange={(event: any) => {
        handleSubmit(event.target.value as string)
      }}
      options={[
        { value: "new", label: "New" },
        { value: "in_progress", label: "In Progress" },
        { value: "resolved", label: "Resolved/Completed" },
      ]}
    />
  )
}

export function CustomAlertSettings({ clientId }: { clientId: string }) {
  const [api] = useApi()

  const [client, setClient] = useState<any>([])
  const [settings, setSettings] = useState<any>([])
  const [thresholds, setThresholds] = useState<any>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchClient()
    fetchAlertSettings()
    fetchThresholds()

    // eslint-disable-next-line
  }, [])

  const fetchClient = async () => {
    try {
      const response = await api({
        method: "GET",
        uri: `${ENDPOINTS.clients}/getstats?id=${clientId}`,
      })

      setClient(response)
    } catch (err) {
    } finally {
    }
  }

  const fetchAlertSettings = async () => {
    try {
      const response = await api({
        method: "GET",
        uri: `${ENDPOINTS.clients}/get_custom_alerts`,
      })

      setSettings(response?.allowed_types)
    } catch (err) {
    } finally {
    }
  }

  const fetchThresholds = async () => {
    try {
      setLoading(true)

      const response = await api({
        method: "GET",
        uri: `${ENDPOINTS.clients}/get_custom_alerts?id=${clientId}`,
      })

      setThresholds(response)
    } catch (err) {
    } finally {
      setLoading(false)
    }
  }

  const onCreate = async () => {
    try {
      setError(null)

      const body = {
        type: "cpu",
        threshold: "0",
        file_system: "",
        client_id: clientId,
      }

      await api({
        method: "POST",
        body: JSON.stringify(body),
        message: "Alert created successfully",
        uri: `${ENDPOINTS.clients}/create_custom_alert`,
      })

      fetchThresholds()
    } catch (error: any) {
      setError(error.message)
    } finally {
    }
  }

  const onUpdate = async (row: any) => {
    try {
      setError(null)

      const body = {
        type: row.type,
        alert_id: row.id,
        client_id: clientId,
        threshold: row.threshold,
        file_system: row.file_system || "",
      }

      await api({
        method: "PUT",
        body: JSON.stringify(body),
        message: "Alert updated successfully",
        uri: `${ENDPOINTS.clients}/update_custom_alert`,
      })
    } catch (error: any) {
      setError(error.message)
    } finally {
    }
  }

  const onDelete = async (row: any) => {
    try {
      setError(null)

      await api({
        method: "DELETE",
        message: "Alert deleted successfully",
        uri: `${ENDPOINTS.clients}/del_custom_alert?client_id=${clientId}&alert_id=${row.id}`,
      })

      setThresholds(thresholds.filter((item: any) => item.id !== row.id))
    } catch (error: any) {
      setError(error.message)
    } finally {
    }
  }

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        flexDirection: "column",
      }}
    >
      {loading ? (
        <Box
          sx={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <CircularProgress />
        </Box>
      ) : (
        <Box sx={{ width: "100%" }}>
          <Grid container spacing={2}>
            {thresholds.map((threshold: any, index: number) => (
              <>
                <Grid item sm={3}>
                  <Select
                    fullWidth
                    size="small"
                    label="Type"
                    value={threshold?.type}
                    onChange={(event: any) => {
                      let rows = [...thresholds]
                      rows[index].type = event.target.value
                      setThresholds(rows)
                    }}
                    options={settings.map((setting: string) => ({
                      value: setting,
                      label: toTitleCase(setting),
                    }))}
                  />
                </Grid>
                <Grid item sm={3}>
                  <TextField
                    fullWidth
                    size="small"
                    id="threshold"
                    name="threshold"
                    label="Threshold"
                    value={threshold?.threshold}
                    onChange={(event: any) => {
                      let rows = [...thresholds]
                      rows[index].threshold = event.target.value
                      setThresholds(rows)
                    }}
                  />
                </Grid>
                <Grid item sm={4}>
                  {threshold.type === "disk" && (
                    <Select
                      fullWidth
                      size="small"
                      label="File System"
                      value={threshold?.file_system}
                      onChange={(event: any) => {
                        let rows = [...thresholds]
                        rows[index].file_system = event.target.value
                        setThresholds(rows)
                      }}
                      options={client?.disks?.map((disk: any) => ({
                        value: disk.filesystem,
                        label: disk.filesystem,
                      }))}
                    />
                  )}
                </Grid>
                <Grid item sm={2} sx={{ textAlign: "right" }}>
                  <IconButton>
                    <Edit
                      color="primary"
                      fontSize="small"
                      onClick={() => onUpdate(threshold)}
                    />
                  </IconButton>
                  <IconButton>
                    <Delete
                      color="error"
                      fontSize="small"
                      onClick={() => onDelete(threshold)}
                    />
                  </IconButton>
                </Grid>
              </>
            ))}
          </Grid>

          <Alert type="error" message={error} />

          <Box
            sx={{
              mt: 2,
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-end",
            }}
          >
            <Button onClick={onCreate}>Add</Button>
          </Box>
        </Box>
      )}
    </Box>
  )
}
