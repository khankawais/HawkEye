export default function SolidSvg({
  path,
  width,
  height,
  fit = false,
  color = "black",
}: {
  path: string
  fit?: boolean
  width: number
  height: number
  color?: string
}) {
  return (
    <div>
      <style jsx>{`
        div {
          width: ${width};
          height: ${height};
          background-color: ${color};
          mask: url(${path});
          mask-position: center;
          mask-repeat: no-repeat;
          mask-size: ${fit ? "contain" : "auto"};
        }
      `}</style>
    </div>
  )
}
