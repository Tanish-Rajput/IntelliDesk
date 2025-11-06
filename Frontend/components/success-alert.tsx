import { CheckCircle2 } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface SuccessAlertProps {
  message: string
}

export default function SuccessAlert({ message }: SuccessAlertProps) {
  return (
    <Alert className="fixed bottom-4 right-4 w-96 border-green-500/50 bg-green-500/10">
      <CheckCircle2 className="w-4 h-4 text-green-600" />
      <AlertDescription className="text-green-600 ml-2">{message}</AlertDescription>
    </Alert>
  )
}
