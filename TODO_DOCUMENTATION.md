# TODO Documentation - Universal Camera Viewer

This document provides a comprehensive overview of all TODO items found in the codebase, organized by priority, feature, and location.

---

## 📊 Summary Statistics

- **Total TODOs Found**: 60+
- **High Priority**: 15
- **Medium Priority**: 25
- **Low Priority**: 20+

---

## 🔴 High Priority TODOs

### 1. **API Integration & Backend Connection**

#### Scanner Service Integration
- **Location**: `src/services/scanner/scannerService.ts`
- **Priority**: HIGH
- **Description**: Multiple scanner endpoints need to be connected to real backend
- **TODOs**:
  - Line 73: Connect with real backend endpoint for network scanning
  - Line 121: Replace mock with real API call for network scan
  - Line 137: Connect with endpoint for stopping scan
  - Line 154: Replace with real stop scan call
  - Line 165: Endpoint for getting scan status
  - Line 201: Get found devices endpoint
  - Line 228: Port scanning endpoint
  - Line 251: Implement real port scan call
  - Line 263: Get port scan results
  - Line 315: Validate credentials endpoint
  - Line 349: Implement real access test call
  - Line 368: Get default credentials list
  - Line 386: Replace with real credentials API call
  - Line 411: Connect with WebSocket for real-time events
  - Line 466-487: Implement store updates for WebSocket messages

#### Settings API Integration
- **Location**: `src/features/settings/components/UserPreferences.tsx`
- **Priority**: HIGH
- **Line**: 76
- **TODO**: Implement real API save for user preferences

- **Location**: `src/features/settings/components/CameraSettings.tsx`
- **Priority**: HIGH
- **Line**: 107
- **TODO**: Implement real API save for camera settings

- **Location**: `src/features/settings/components/NetworkSettings.tsx`
- **Priority**: HIGH
- **Line**: 72
- **TODO**: Implement real API save for network settings

### 2. **Camera Functionality**

#### Snapshot Capture
- **Location**: `src/hooks/useCamera.ts`
- **Priority**: HIGH
- **Line**: 133
- **TODO**: Implement snapshot capture in v2

- **Location**: `src/features/cameras/CamerasPage.tsx`
- **Priority**: HIGH
- **Line**: 133
- **TODO**: Implement capture with API v2

#### Camera Connection
- **Location**: `src/features/cameras/pages/LiveViewPage.tsx`
- **Priority**: HIGH
- **Line**: 187
- **TODO**: Implement connect all cameras functionality
- **Line**: 201
- **TODO**: Implement disconnect all cameras functionality

### 3. **Store Integration**

#### Navigation Store
- **Location**: `src/stores/appStore.ts`
- **Priority**: HIGH
- **Line**: 48
- **TODO**: Generate breadcrumbs based on path

---

## 🟡 Medium Priority TODOs

### 1. **UI Components & Features**

#### Quick Settings Menu
- **Location**: `src/components/menus/QuickSettingsMenu.tsx`
- **Priority**: MEDIUM
- **Line**: 68
- **TODO**: Connect all controls with settings store and backend
- **Line**: 83
- **TODO**: Implement persistence and sound test
- **Line**: 98
- **TODO**: Apply quality to active streams
- **Line**: 111
- **TODO**: Configure notification permissions
- **Line**: 125
- **TODO**: Internationalization system (i18n)
- **Line**: 139
- **TODO**: Open folder with Tauri
- **Line**: 152
- **TODO**: Navigate to full settings

#### Settings Page Components
- **Location**: `src/features/settings/SettingsPage.tsx`
- **Priority**: MEDIUM
- **Line**: 38
- **TODO**: Implement ProtocolSettings and BackupSettings components
- **Line**: 278
- **TODO**: Implement these components when backend is complete

#### Camera Configuration Modal
- **Location**: `src/features/cameras/CamerasPage.tsx`
- **Priority**: MEDIUM
- **Line**: 128
- **TODO**: Implement camera configuration modal

### 2. **Data Management**

#### Import/Export Features
- **Location**: `src/features/cameras/components/management/ManagementToolbar.tsx`
- **Priority**: MEDIUM
- **Multiple TODOs**: Import CSV, export data, batch operations

#### License & About Dialogs
- **Location**: `src/components/dialogs/AboutDialog.tsx`
- **Priority**: MEDIUM
- **Line**: 159
- **TODO**: Connect with real update service
- **Line**: 753
- **TODO**: Implement update download
- **Line**: 856
- **TODO**: Implement programmatic navigation to settings
- **Line**: 981
- **TODO**: Implement license export

### 3. **Network Features**

#### Scanner Component Integration
- **Location**: `src/features/scanner/components/NetworkScanPanel.tsx`
- **Priority**: MEDIUM
- **Multiple TODOs**: Implement real scanner integration

#### Port Scanning
- **Location**: `src/features/scanner/components/PortScanPanel.tsx`
- **Priority**: MEDIUM
- **Multiple TODOs**: Implement port scanning features

#### Access Testing
- **Location**: `src/features/scanner/components/AccessTestPanel.tsx`
- **Priority**: MEDIUM
- **Multiple TODOs**: Implement access testing features

---

## 🟢 Low Priority TODOs

### 1. **UI Enhancements**

#### Map View
- **Location**: `src/features/cameras/components/management/CameraMapView.tsx`
- **Priority**: LOW
- **TODO**: Implement interactive map view for cameras

#### Themes & Styling
- **Various locations**
- **Priority**: LOW
- **TODOs**: Theme switching, custom styling options

### 2. **Documentation & Comments**

#### Code Comments
- **Location**: `src/features/cameras/pages/LiveViewPage.tsx`
- **Priority**: LOW
- **Line**: 82
- **TODO**: Filter only connected cameras in the future

### 3. **Future Features**

#### Advanced Analytics
- **Various locations**
- **Priority**: LOW
- **TODOs**: Analytics dashboard, usage statistics

---

## 📋 TODO by Module/Feature

### Camera Module
- Snapshot capture implementation
- Camera configuration modal
- Connect/disconnect all cameras
- Live view filtering

### Settings Module
- User preferences API integration
- Camera settings API integration
- Network settings API integration
- Protocol settings component
- Backup settings component

### Scanner Module
- Network scan API integration
- Port scan implementation
- Access test implementation
- WebSocket real-time updates
- Default credentials management

### UI Components
- Quick settings menu integration
- Notification system
- Internationalization (i18n)
- Theme switching
- Tauri folder operations

### Data Management
- Import/Export functionality
- Batch operations
- License management

### Update System
- Check for updates integration
- Download updates
- Auto-update mechanism

---

## 🚀 Implementation Recommendations

### Phase 1 - Critical Backend Integration (Week 1-2)
1. Scanner Service API endpoints
2. Settings persistence API
3. Camera snapshot functionality
4. WebSocket for real-time updates

### Phase 2 - Core Features (Week 3-4)
1. Connect/disconnect all cameras
2. Camera configuration modal
3. Import/Export functionality
4. Notification system

### Phase 3 - Enhanced Features (Week 5-6)
1. Internationalization
2. Theme system
3. Update mechanism
4. Advanced settings components

### Phase 4 - Polish & Optimization (Week 7-8)
1. Performance optimizations
2. Error handling improvements
3. UI/UX refinements
4. Documentation updates

---

## 📌 Notes

- Most TODOs are related to backend integration, indicating the frontend is mostly complete
- Scanner service has the most TODOs and should be prioritized
- Many TODOs include detailed implementation suggestions in comments
- Consider creating GitHub issues from high-priority TODOs for better tracking

---

*Last Updated: 2025-07-18*