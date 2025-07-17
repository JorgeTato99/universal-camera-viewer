/**
 * 🎯 License Dialog Component - Universal Camera Viewer
 * Dialog para mostrar la licencia completa del software
 */

import React from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  Button,
  IconButton,
  useTheme,
  alpha,
  Fade,
} from "@mui/material";
import {
  Close as CloseIcon,
  Print as PrintIcon,
  Download as DownloadIcon,
} from "@mui/icons-material";
import { colorTokens, borderTokens } from "../../design-system/tokens";

interface LicenseDialogProps {
  open: boolean;
  onClose: () => void;
}

const FULL_LICENSE_TEXT = `ACUERDO DE LICENCIA DE SOFTWARE PROPIETARIO
UNIVERSAL CAMERA VIEWER
Version 1.0 - Enero 2025

IMPORTANTE: LEA CUIDADOSAMENTE ESTE ACUERDO DE LICENCIA ANTES DE USAR EL SOFTWARE.

Este Acuerdo de Licencia de Software ("Acuerdo") es un contrato legal entre usted (ya sea una persona física o jurídica) y Kipustec S.A. de C.V. ("Kipustec") para el software Universal Camera Viewer, que incluye el software informático y puede incluir medios asociados, materiales impresos y documentación en línea o electrónica ("Software").

Al instalar, copiar o utilizar el Software, usted acepta quedar vinculado por los términos de este Acuerdo. Si no está de acuerdo con los términos de este Acuerdo, no instale ni utilice el Software.

1. CONCESIÓN DE LICENCIA
Sujeto a los términos y condiciones de este Acuerdo, Kipustec le otorga una licencia no exclusiva, no transferible y revocable para:
a) Instalar y usar una copia del Software en un único dispositivo.
b) Hacer una copia del Software únicamente con fines de respaldo.
c) Usar el Software únicamente para los fines para los que fue diseñado.

2. RESTRICCIONES DE USO
Usted NO puede:
a) Copiar o reproducir el Software, excepto como se permite expresamente en este Acuerdo.
b) Modificar, adaptar, traducir o crear trabajos derivados basados en el Software.
c) Realizar ingeniería inversa, descompilar, desensamblar o intentar descubrir el código fuente del Software.
d) Alquilar, arrendar, prestar, vender, sublicenciar o distribuir el Software.
e) Eliminar o alterar avisos de propiedad o etiquetas del Software.
f) Usar el Software para fines ilegales o no autorizados.
g) Usar el Software en sistemas críticos donde el fallo podría causar daños a personas o propiedad.

3. PROPIEDAD INTELECTUAL
El Software es propiedad de Kipustec y está protegido por las leyes de derechos de autor de México y tratados internacionales. Kipustec retiene todos los derechos no expresamente otorgados a usted en este Acuerdo.

4. ACTUALIZACIONES Y SOPORTE
a) Kipustec puede proporcionar actualizaciones, parches o nuevas versiones del Software a su discreción.
b) El soporte técnico se proporciona según los términos de servicio vigentes de Kipustec.
c) Las actualizaciones están sujetas a este Acuerdo a menos que vengan con un acuerdo de licencia separado.

5. RECOPILACIÓN DE DATOS
El Software puede recopilar información sobre:
a) Configuración del sistema y hardware
b) Uso del Software y estadísticas de rendimiento
c) Información de diagnóstico para mejorar el Software
Esta información se recopila de forma anónima y se utiliza únicamente para mejorar el Software.

6. GARANTÍA LIMITADA
EL SOFTWARE SE PROPORCIONA "TAL CUAL" SIN GARANTÍAS DE NINGÚN TIPO, YA SEAN EXPRESAS O IMPLÍCITAS, INCLUYENDO, PERO NO LIMITADO A, LAS GARANTÍAS IMPLÍCITAS DE COMERCIABILIDAD E IDONEIDAD PARA UN PROPÓSITO PARTICULAR.

7. LIMITACIÓN DE RESPONSABILIDAD
EN NINGÚN CASO KIPUSTEC SERÁ RESPONSABLE POR DAÑOS ESPECIALES, INCIDENTALES, INDIRECTOS O CONSECUENTES (INCLUYENDO, SIN LIMITACIÓN, DAÑOS POR PÉRDIDA DE BENEFICIOS, INTERRUPCIÓN DEL NEGOCIO, PÉRDIDA DE INFORMACIÓN COMERCIAL U OTRA PÉRDIDA PECUNIARIA) QUE SURJAN DEL USO O LA IMPOSIBILIDAD DE USAR EL SOFTWARE.

8. TERMINACIÓN
Este Acuerdo permanecerá en vigor hasta su terminación. Kipustec puede terminar este Acuerdo inmediatamente si usted incumple cualquiera de sus términos. Tras la terminación, debe dejar de usar el Software y destruir todas las copias.

9. LEY APLICABLE
Este Acuerdo se regirá por las leyes de México. Cualquier disputa relacionada con este Acuerdo se resolverá en los tribunales competentes de la Ciudad de México.

10. ACUERDO COMPLETO
Este Acuerdo constituye el acuerdo completo entre las partes y reemplaza todos los acuerdos anteriores relacionados con el Software.

11. CONTACTO
Si tiene preguntas sobre este Acuerdo, contacte a:
Kipustec S.A. de C.V.
Email: legal@kipustec.com
Teléfono: +52 (55) 1234-5678

Al usar el Software, usted reconoce que ha leído este Acuerdo, lo entiende y acepta estar sujeto a sus términos y condiciones.

© 2025 Kipustec S.A. de C.V. Todos los derechos reservados.
Universal Camera Viewer® es una marca registrada de Kipustec S.A. de C.V.`;

export const LicenseDialog: React.FC<LicenseDialogProps> = ({ open, onClose }) => {
  const theme = useTheme();

  const handlePrint = () => {
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(`
        <html>
          <head>
            <title>Licencia - ${APP_CONFIG.app.name}</title>
            <style>
              body { font-family: Arial, sans-serif; padding: 20px; white-space: pre-wrap; }
              h1 { text-align: center; }
            </style>
          </head>
          <body>
            <h1>LICENCIA DE SOFTWARE</h1>
            <pre>${FULL_LICENSE_TEXT}</pre>
          </body>
        </html>
      `);
      printWindow.document.close();
      printWindow.print();
    }
  };

  const handleDownload = () => {
    const blob = new Blob([FULL_LICENSE_TEXT], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${APP_CONFIG.app.name.replace(/ /g, '_')}_Licencia.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      TransitionComponent={Fade}
      PaperProps={{
        sx: {
          borderRadius: borderTokens.radius.lg,
          maxHeight: "90vh",
        },
      }}
    >
      <DialogTitle
        sx={{
          m: 0,
          p: 2,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
          Licencia de Software
        </Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <IconButton
            size="small"
            onClick={handlePrint}
            sx={{
              color: theme.palette.text.secondary,
              transition: "all 0.3s ease",
              "&:hover": {
                backgroundColor: alpha(colorTokens.primary[500], 0.1),
                color: colorTokens.primary[500],
              },
            }}
            aria-label="Imprimir licencia"
          >
            <PrintIcon />
          </IconButton>
          <IconButton
            size="small"
            onClick={handleDownload}
            sx={{
              color: theme.palette.text.secondary,
              transition: "all 0.3s ease",
              "&:hover": {
                backgroundColor: alpha(colorTokens.primary[500], 0.1),
                color: colorTokens.primary[500],
              },
            }}
            aria-label="Descargar licencia"
          >
            <DownloadIcon />
          </IconButton>
          <IconButton
            onClick={onClose}
            size="small"
            sx={{
              color: theme.palette.text.secondary,
              transition: "all 0.3s ease",
              "&:hover": {
                backgroundColor: alpha(theme.palette.action.hover, 0.5),
                transform: "rotate(90deg)",
              },
            }}
            aria-label="Cerrar"
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent sx={{ p: 3 }}>
        <Box
          sx={{
            backgroundColor: theme.palette.mode === "dark"
              ? "rgba(255, 255, 255, 0.02)"
              : "rgba(0, 0, 0, 0.01)",
            borderRadius: borderTokens.radius.md,
            p: 3,
            fontFamily: "monospace",
            fontSize: "0.875rem",
            lineHeight: 1.6,
            whiteSpace: "pre-wrap",
            overflowY: "auto",
            maxHeight: "60vh",
            border: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Typography
            component="pre"
            sx={{
              m: 0,
              fontFamily: "inherit",
              fontSize: "inherit",
              color: theme.palette.text.primary,
            }}
          >
            {FULL_LICENSE_TEXT}
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions
        sx={{
          p: 2,
          borderTop: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Button
          onClick={onClose}
          variant="contained"
          sx={{
            textTransform: "none",
            borderRadius: borderTokens.radius.md,
            minWidth: 100,
          }}
        >
          Cerrar
        </Button>
      </DialogActions>
    </Dialog>
  );
};