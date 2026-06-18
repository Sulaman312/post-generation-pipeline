import { useEffect, useState } from "react";
import "./App.css";
import AppSidebar from "./components/shared/AppSidebar";
import ClientsGrid from "./components/workspace/ClientsGrid";
import ClientHome from "./components/workspace/ClientHome";
import RunView from "./components/run/RunView";
import WorkspaceDashboard from "./components/workspace/WorkspaceDashboard";
import ContentPipelineBoard from "./components/workspace/ContentPipelineBoard";
import SocialPipelineBoard from "./components/workspace/SocialPipelineBoard";
import StepMatrixScreen from "./components/run/StepMatrixScreen";
import SocialStepMatrixScreen from "./components/run/SocialStepMatrixScreen";
import { ToastProvider } from "./context/ToastContext";
import { CONTENTFLOW_LOGO } from "./constants/brand";
import {
  appProductMeta,
  lockedActivePipeline,
} from "./constants/appProject";
import { readStoredSidebarWidth } from "./hooks/useSidebarResize";

const LOCKED_PIPELINE = lockedActivePipeline();
const PRODUCT = appProductMeta();

function App() {
  const [client, setClient] = useState(null);
  const [runId, setRunId] = useState(null);
  const [activeStepKey, setActiveStepKey] = useState("topic_card");
  const [clientsRefresh, setClientsRefresh] = useState(0);
  const [workspaceView, setWorkspaceView] = useState("overview");
  const [artifactFilename, setArtifactFilename] = useState(null);
  /** null = pipeline picker; "content" = content generation article board */
  const [activePipeline, setActivePipeline] = useState(null);
  const [logoVersions, setLogoVersions] = useState({});
  /** Optimistic step status while pause/cancel is in flight (cleared when run reloads). */
  const [stepStatusOverrides, setStepStatusOverrides] = useState({});

  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try {
      return localStorage.getItem("cf-sidebar-collapsed") === "1";
    } catch {
      return false;
    }
  });

  const [sidebarWidth, setSidebarWidth] = useState(readStoredSidebarWidth);

  useEffect(() => {
    try {
      localStorage.setItem(
        "cf-sidebar-collapsed",
        sidebarCollapsed ? "1" : "0"
      );
    } catch {
      /* ignore */
    }
  }, [sidebarCollapsed]);

  useEffect(() => {
    if (sidebarCollapsed) return;
    try {
      localStorage.setItem("cf-sidebar-width", String(sidebarWidth));
    } catch {
      /* ignore */
    }
  }, [sidebarWidth, sidebarCollapsed]);

  function goHome() {
    setClient(null);
    setRunId(null);
    setWorkspaceView("overview");
    setArtifactFilename(null);
    setActivePipeline(null);
  }

  function handleClientDeleted() {
    goHome();
    setClientsRefresh((n) => n + 1);
  }

  function bumpClientLogo(clientId) {
    setLogoVersions((v) => ({ ...v, [clientId]: Date.now() }));
  }

  function openClient(c) {
    setClient(c);
    setRunId(null);
    setWorkspaceView("overview");
    setArtifactFilename(null);
    setActivePipeline(null);
  }

  function openRun(id) {
    setRunId(id);
    setActiveStepKey("topic_card");
    setStepStatusOverrides({});
  }

  function patchStepStatus(stepKey, status) {
    if (stepKey == null && status == null) {
      setStepStatusOverrides({});
      return;
    }
    setStepStatusOverrides((prev) => {
      if (status == null) {
        if (!(stepKey in prev)) return prev;
        const next = { ...prev };
        delete next[stepKey];
        return next;
      }
      return { ...prev, [stepKey]: status };
    });
  }

  function closeRun() {
    setRunId(null);
    setStepStatusOverrides({});
    if (activePipeline === "content") {
      setWorkspaceView("matrix");
    } else if (activePipeline === "social") {
      setWorkspaceView("matrix");
    }
  }

  function handleWorkspaceViewChange(view) {
    setWorkspaceView(view);
    setArtifactFilename(null);
  }

  function goToEditorial() {
    setRunId(null);
    setActivePipeline("content");
    setWorkspaceView("overview");
    setArtifactFilename(null);
  }

  function goToSocialBoard() {
    setRunId(null);
    setActivePipeline("social");
    setWorkspaceView("overview");
    setArtifactFilename(null);
  }

  function goToMatrix() {
    setRunId(null);
    setActivePipeline("content");
    setWorkspaceView("matrix");
    setArtifactFilename(null);
  }

  function goToSocialMatrix() {
    setRunId(null);
    setActivePipeline("social");
    setWorkspaceView("matrix");
    setArtifactFilename(null);
  }

  function goToArtifacts() {
    setRunId(null);
    setActivePipeline((prev) => prev ?? LOCKED_PIPELINE);
    setWorkspaceView("artifacts");
    setArtifactFilename(null);
  }

  function goToPipeline() {
    setRunId(null);
    setActivePipeline(null);
    setWorkspaceView("overview");
    setArtifactFilename(null);
  }

  if (!client) {
    return (
      <div className="layout-flat">
        <header className="topbar">
          <div className="topbar-brand" onClick={goHome}>
            <img
              className="topbar-mark-img"
              src={CONTENTFLOW_LOGO}
              alt="ContentFlow"
              width={36}
              height={36}
            />
            <div className="topbar-name">
              {PRODUCT.name}
              <span className="topbar-meta">{PRODUCT.workspaceTagline}</span>
            </div>
          </div>
        </header>
        <main className="layout-main">
          <ClientsGrid
            key={clientsRefresh}
            onOpenClient={openClient}
            logoVersions={logoVersions}
            onClientLogoSaved={bumpClientLogo}
          />
        </main>
      </div>
    );
  }

  return (
    <div
      className={`layout${sidebarCollapsed ? " layout--sb-collapsed" : ""}`}
      style={
        sidebarCollapsed
          ? undefined
          : { "--sidebar-w": `${sidebarWidth}px` }
      }
    >
      <AppSidebar
        client={client}
        runId={runId}
        collapsed={sidebarCollapsed}
        sidebarWidth={sidebarWidth}
        onSidebarWidthChange={setSidebarWidth}
        onToggleCollapse={() => setSidebarCollapsed((v) => !v)}
        activeStepKey={activeStepKey}
        onSelectStep={setActiveStepKey}
        onGoHome={goHome}
        onClearRun={closeRun}
        workspaceView={workspaceView}
        onWorkspaceViewChange={handleWorkspaceViewChange}
        onGoToEditorial={goToEditorial}
        onGoToMatrix={goToMatrix}
        onGoToSocialBoard={goToSocialBoard}
        onGoToSocialMatrix={goToSocialMatrix}
        onGoToArtifacts={goToArtifacts}
        onGoToPipeline={goToPipeline}
        activePipeline={activePipeline}
        lockedPipeline={LOCKED_PIPELINE}
        logoVersion={logoVersions[client] || 0}
        onPatchStepStatus={patchStepStatus}
        stepStatusOverrides={stepStatusOverrides}
      />
      <main className="layout-main">
        {!runId &&
        workspaceView === "artifacts" &&
        (activePipeline === null ||
          activePipeline === "social" ||
          activePipeline === "content") ? (
          <ClientHome
            client={client}
            onOpenRun={openRun}
            onClientDeleted={handleClientDeleted}
            workspaceView={workspaceView}
            artifactFilename={artifactFilename}
            onArtifactFilenameChange={setArtifactFilename}
          />
        ) : !runId && activePipeline === null && workspaceView !== "artifacts" ? (
          <WorkspaceDashboard
            client={client}
            onClientDeleted={handleClientDeleted}
            onSelectContent={() => {
              setActivePipeline("content");
              setWorkspaceView("matrix");
              setArtifactFilename(null);
            }}
            onSelectSocial={() => {
              setActivePipeline("social");
              setWorkspaceView("matrix");
              setArtifactFilename(null);
            }}
          />
        ) : !runId &&
          activePipeline === "content" &&
          workspaceView === "matrix" ? (
          <StepMatrixScreen
            client={client}
            onOpenRun={openRun}
            onClientDeleted={handleClientDeleted}
            onBackToBoard={() => setWorkspaceView("overview")}
          />
        ) : !runId &&
          activePipeline === "social" &&
          workspaceView === "matrix" ? (
          <SocialStepMatrixScreen
            client={client}
            onOpenRun={openRun}
            onClientDeleted={handleClientDeleted}
            onBackToBoard={() => setWorkspaceView("overview")}
          />
        ) : !runId &&
          activePipeline === "content" &&
          workspaceView === "overview" ? (
          <ContentPipelineBoard
            client={client}
            onOpenRun={openRun}
            onClientDeleted={handleClientDeleted}
          />
        ) : !runId &&
          activePipeline === "social" &&
          workspaceView === "overview" ? (
          <SocialPipelineBoard
            client={client}
            onOpenRun={openRun}
            onClientDeleted={handleClientDeleted}
          />
        ) : !runId ? (
          <ClientHome
            client={client}
            onOpenRun={openRun}
            onClientDeleted={handleClientDeleted}
            workspaceView={workspaceView}
            artifactFilename={artifactFilename}
            onArtifactFilenameChange={setArtifactFilename}
          />
        ) : (
          <RunView
            client={client}
            runId={runId}
            activeStepKey={activeStepKey}
            statusOverrides={stepStatusOverrides}
            onSelectStep={setActiveStepKey}
            onBack={() => {
              closeRun();
              setWorkspaceView("matrix");
            }}
          />
        )}
      </main>
    </div>
  );
}

export default function AppWithToast() {
  return (
    <ToastProvider>
      <App />
    </ToastProvider>
  );
}
