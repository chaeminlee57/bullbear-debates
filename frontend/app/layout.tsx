export const metadata = {
  title: 'BullBear Debates',
  description: 'Real-time market sentiment dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
