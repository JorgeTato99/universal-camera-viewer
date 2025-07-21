/**
 * 🔗 MediaMTX URL Input Component - Universal Camera Viewer
 * Input con validación de formato para URLs MediaMTX
 */

import React, { memo, useState, useEffect } from 'react';
import {
  TextField,
  InputAdornment,
  IconButton,
  Tooltip,
  Box,
  Typography,
  Chip
} from '@mui/material';
import {
  Link as LinkIcon,
  CheckCircle as ValidIcon,
  Error as ErrorIcon,
  Help as HelpIcon
} from '@mui/icons-material';
import { validateMediaMTXUrl } from '../../utils';

interface MediaMTXUrlInputProps {
  value: string;
  onChange: (value: string) => void;
  onValidate?: (isValid: boolean) => void;
  label?: string;
  error?: string;
  helperText?: string;
  required?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  showProtocolChips?: boolean;
}

const SUPPORTED_PROTOCOLS = [
  { value: 'rtsp://', label: 'RTSP', color: '#2196f3' },
  { value: 'rtmp://', label: 'RTMP', color: '#4caf50' },
  { value: 'http://', label: 'HTTP', color: '#ff9800' },
  { value: 'https://', label: 'HTTPS', color: '#f44336' }
];

/**
 * Input especializado para URLs MediaMTX
 */
export const MediaMTXUrlInput = memo<MediaMTXUrlInputProps>(({
  value,
  onChange,
  onValidate,
  label = 'URL MediaMTX',
  error,
  helperText,
  required = false,
  disabled = false,
  fullWidth = true,
  showProtocolChips = true
}) => {
  const [isValid, setIsValid] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  useEffect(() => {
    const valid = validateMediaMTXUrl(value);
    setIsValid(valid);
    onValidate?.(valid);
  }, [value, onValidate]);

  const handleProtocolClick = (protocol: string) => {
    if (!value || value.indexOf('://') === -1) {
      onChange(protocol + 'localhost:8554');
    } else {
      const currentUrl = value.substring(value.indexOf('://') + 3);
      onChange(protocol + currentUrl);
    }
  };

  const getValidationIcon = () => {
    if (!value) return null;
    
    return isValid ? (
      <Tooltip title="URL válida">
        <ValidIcon color="success" />
      </Tooltip>
    ) : (
      <Tooltip title="URL inválida">
        <ErrorIcon color="error" />
      </Tooltip>
    );
  };

  return (
    <Box>
      <TextField
        label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        error={!!error || (!isValid && !!value)}
        helperText={error || helperText || (showHelp && 'Formato: protocolo://host:puerto/path')}
        required={required}
        disabled={disabled}
        fullWidth={fullWidth}
        placeholder="rtsp://localhost:8554"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <LinkIcon color="action" />
            </InputAdornment>
          ),
          endAdornment: (
            <InputAdornment position="end">
              {getValidationIcon()}
              <Tooltip title="Ayuda">
                <IconButton
                  size="small"
                  onClick={() => setShowHelp(!showHelp)}
                  edge="end"
                >
                  <HelpIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </InputAdornment>
          )
        }}
      />

      {showProtocolChips && (
        <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
            Protocolos:
          </Typography>
          {SUPPORTED_PROTOCOLS.map((protocol) => (
            <Chip
              key={protocol.value}
              label={protocol.label}
              size="small"
              onClick={() => handleProtocolClick(protocol.value)}
              disabled={disabled}
              sx={{
                cursor: disabled ? 'default' : 'pointer',
                bgcolor: value.startsWith(protocol.value) ? protocol.color : undefined,
                color: value.startsWith(protocol.value) ? 'white' : undefined,
                '&:hover': {
                  bgcolor: value.startsWith(protocol.value) 
                    ? protocol.color 
                    : `${protocol.color}20`
                }
              }}
            />
          ))}
        </Box>
      )}

      {showHelp && (
        <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
          <Typography variant="caption" sx={{ display: 'block', mb: 1 }}>
            <strong>Ejemplos de URLs válidas:</strong>
          </Typography>
          <Typography variant="caption" component="div" sx={{ fontFamily: 'monospace' }}>
            • rtsp://localhost:8554/mystream<br />
            • rtmp://192.168.1.100:1935/live<br />
            • http://media.example.com:8080/hls<br />
            • https://secure.example.com/stream
          </Typography>
        </Box>
      )}
    </Box>
  );
});

MediaMTXUrlInput.displayName = 'MediaMTXUrlInput';