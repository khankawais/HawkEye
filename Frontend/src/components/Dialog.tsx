import * as React from "react"
import { useState } from "react"

import CloseIcon from "@mui/icons-material/Close"
import { Dialog as MuiDialog } from "@mui/material"
import DialogTitle from "@mui/material/DialogTitle"
import { SxProps, Theme } from "@mui/material/styles"
import DialogContent from "@mui/material/DialogContent"

import { IconButton } from "@components/IconButton"

// import { useWindowResize } from "@hooks/useWindowResize"

interface DialogProps {
  title: string
  fullWidth?: boolean
  sx?: SxProps<Theme>
  onClose?: () => void
  trigger: (args: any) => void
  maxWidth?: "xs" | "sm" | "md" | "lg" | "xl"
  content: (args: any) => React.ReactNode | React.ReactNode
}

export const Dialog = ({
  sx,
  title,
  onClose,
  trigger,
  content,
  fullWidth,
  maxWidth = "xs",
}: DialogProps) => {
  // const [width] = useWindowResize()
  const [open, setOpen] = useState(false)

  const toggleOpen = () => {
    setOpen(!open)
    if (open && onClose) {
      onClose()
    }
  }

  return (
    <>
      {trigger({ toggleOpen })}
      <MuiDialog
        sx={sx}
        open={open}
        maxWidth={maxWidth}
        onClose={toggleOpen}
        fullWidth={fullWidth}
      >
        <DialogTitle id={`dialog-${title}`}>{title}</DialogTitle>
        <IconButton
          aria-label="close"
          onClick={toggleOpen}
          sx={{
            top: 8,
            right: 8,
            position: "absolute",
          }}
        >
          <CloseIcon />
        </IconButton>

        <DialogContent
          // Shouldn't overflow when screen is small
          sx={(theme: Theme) => ({
            // width:
            //   theme.breakpoints.values.xs > width
            //     ? width - +theme.spacing(8).replace("px", "")
            //     : theme.breakpoints.values.xs,
            width: "100%",
          })}
        >
          {typeof content === "function"
            ? content({ onClose: toggleOpen })
            : content}
        </DialogContent>
      </MuiDialog>
    </>
  )
}
