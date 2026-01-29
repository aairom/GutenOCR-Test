# GutenOCR Application Flow Charts

This document contains detailed Mermaid flow charts for the GutenOCR application.

## Table of Contents

1. [Application Startup Flow](#application-startup-flow)
2. [Single Image Processing Flow](#single-image-processing-flow)
3. [Batch Processing Flow](#batch-processing-flow)
4. [Combined Docling + GutenOCR Flow](#combined-docling--gutenocr-flow)
5. [Docker Deployment Flow](#docker-deployment-flow)
6. [Kubernetes Deployment Flow](#kubernetes-deployment-flow)
7. [Error Handling Flow](#error-handling-flow)

## Application Startup Flow

```mermaid
flowchart TD
    Start([Start Application]) --> CheckMode{Check Mode}
    
    CheckMode -->|Gradio| InitGradio[Initialize Gradio UI]
    CheckMode -->|Combined| InitCombined[Initialize Combined Processor]
    CheckMode -->|Docker| InitDocker[Initialize Docker Container]
    CheckMode -->|K8s| InitK8s[Initialize Kubernetes Pod]
    
    InitGradio --> LoadUI[Load Web Interface]
    LoadUI --> WaitUser[Wait for User Input]
    
    WaitUser --> UserAction{User Action}
    UserAction -->|Initialize Model| LoadModel[Load GutenOCR Model]
    UserAction -->|Process Image| ProcessSingle[Process Single Image]
    UserAction -->|Batch Process| ProcessBatch[Process Batch]
    
    LoadModel --> CheckDevice{Check Device}
    CheckDevice -->|CPU| LoadCPU[Load Model on CPU]
    CheckDevice -->|GPU| CheckGPU{GPU Available?}
    
    CheckGPU -->|Yes| LoadGPU[Load Model on GPU]
    CheckGPU -->|No| FallbackCPU[Fallback to CPU]
    
    LoadCPU --> ModelReady[Model Ready]
    LoadGPU --> ModelReady
    FallbackCPU --> ModelReady
    
    ModelReady --> DisplayInfo[Display Device Info]
    DisplayInfo --> WaitUser
    
    InitCombined --> LoadBoth[Load Docling + GutenOCR]
    LoadBoth --> DiscoverFiles[Discover Input Files]
    DiscoverFiles --> ProcessFiles[Process All Files]
    ProcessFiles --> SaveResults[Save Results]
    SaveResults --> End([End])
    
    InitDocker --> PullImage[Pull Docker Image]
    PullImage --> StartContainer[Start Container]
    StartContainer --> MountVolumes[Mount Volumes]
    MountVolumes --> RunApp[Run Application]
    RunApp --> Healthy{Health Check}
    Healthy -->|Pass| Ready[Container Ready]
    Healthy -->|Fail| Restart[Restart Container]
    Restart --> RunApp
    Ready --> End
    
    InitK8s --> CreatePVC[Create PVCs]
    CreatePVC --> CreateConfigMap[Create ConfigMap]
    CreateConfigMap --> CreateDeployment[Create Deployment]
    CreateDeployment --> CreateService[Create Service]
    CreateService --> CreateIngress[Create Ingress]
    CreateIngress --> WaitPods{Pods Ready?}
    WaitPods -->|Yes| K8sReady[Kubernetes Ready]
    WaitPods -->|No| WaitMore[Wait for Pods]
    WaitMore --> WaitPods
    K8sReady --> End
```

## Single Image Processing Flow

```mermaid
flowchart TD
    Start([User Uploads Image]) --> ValidateImage{Valid Image?}
    
    ValidateImage -->|No| ErrorFormat[Error: Invalid Format]
    ValidateImage -->|Yes| CheckModel{Model Loaded?}
    
    ErrorFormat --> DisplayError[Display Error Message]
    DisplayError --> End([End])
    
    CheckModel -->|No| ErrorModel[Error: Model Not Loaded]
    CheckModel -->|Yes| GetOptions[Get Task Type & Format]
    
    ErrorModel --> DisplayError
    
    GetOptions --> PrepareInput[Prepare Input]
    PrepareInput --> LoadImage[Load Image to Memory]
    LoadImage --> CreatePrompt[Create Prompt]
    CreatePrompt --> ProcessVision[Process Vision Info]
    
    ProcessVision --> Tokenize[Tokenize Input]
    Tokenize --> MoveDevice[Move to Device]
    MoveDevice --> Generate[Generate Output]
    
    Generate --> CheckSuccess{Success?}
    
    CheckSuccess -->|No| ErrorProcess[Processing Error]
    CheckSuccess -->|Yes| DecodeOutput[Decode Output]
    
    ErrorProcess --> LogError[Log Error]
    LogError --> DisplayError
    
    DecodeOutput --> FormatResult[Format Result]
    FormatResult --> DisplayResult[Display Result]
    DisplayResult --> OfferSave{Save Result?}
    
    OfferSave -->|Yes| SaveFile[Save to Output]
    OfferSave -->|No| End
    
    SaveFile --> Timestamp[Add Timestamp]
    Timestamp --> WriteFile[Write File]
    WriteFile --> Confirm[Confirm Save]
    Confirm --> End
```

## Batch Processing Flow

```mermaid
flowchart TD
    Start([Start Batch Processing]) --> CheckModel{Model Loaded?}
    
    CheckModel -->|No| ErrorModel[Error: Model Not Loaded]
    CheckModel -->|Yes| GetOptions[Get Processing Options]
    
    ErrorModel --> End([End])
    
    GetOptions --> DiscoverImages[Discover Images in Input Dir]
    DiscoverImages --> CheckImages{Images Found?}
    
    CheckImages -->|No| ErrorNoImages[Error: No Images Found]
    CheckImages -->|Yes| InitResults[Initialize Results List]
    
    ErrorNoImages --> End
    
    InitResults --> InitProgress[Initialize Progress Bar]
    InitProgress --> LoopStart{More Images?}
    
    LoopStart -->|No| AllProcessed[All Images Processed]
    LoopStart -->|Yes| GetNextImage[Get Next Image]
    
    GetNextImage --> UpdateProgress[Update Progress]
    UpdateProgress --> ProcessImage[Process Image]
    
    ProcessImage --> CheckResult{Success?}
    
    CheckResult -->|Yes| AddSuccess[Add to Results]
    CheckResult -->|No| AddFailure[Add Error to Results]
    
    AddSuccess --> LoopStart
    AddFailure --> LoopStart
    
    AllProcessed --> GenerateStats[Generate Statistics]
    GenerateStats --> SaveCombined[Save Combined Results]
    SaveCombined --> SaveIndividual[Save Individual Files]
    SaveIndividual --> CreateSummary[Create Summary Report]
    
    CreateSummary --> DisplaySummary[Display Summary]
    DisplaySummary --> End
```

## Combined Docling + GutenOCR Flow

```mermaid
flowchart TD
    Start([Start Combined Processing]) --> InitProcessors[Initialize Both Processors]
    
    InitProcessors --> CheckDocling{Docling Available?}
    
    CheckDocling -->|No| GutenOCROnly[GutenOCR Only Mode]
    CheckDocling -->|Yes| BothMode[Combined Mode]
    
    GutenOCROnly --> ProcessOCR[Process with GutenOCR]
    ProcessOCR --> SaveOCRResults[Save OCR Results]
    SaveOCRResults --> End([End])
    
    BothMode --> GetFile[Get Document File]
    GetFile --> ProcessDocling[Process with Docling]
    
    ProcessDocling --> ExtractStructure[Extract Document Structure]
    ExtractStructure --> ExtractTables[Extract Tables]
    ExtractTables --> DoclingDone[Docling Processing Done]
    
    DoclingDone --> ProcessGutenOCR[Process with GutenOCR]
    ProcessGutenOCR --> ExtractText[Extract Text with OCR]
    ExtractText --> GutenOCRDone[GutenOCR Processing Done]
    
    GutenOCRDone --> MergeResults[Merge Results]
    
    MergeResults --> CombineStructure[Combine Structure]
    CombineStructure --> CombineTables[Combine Tables]
    CombineTables --> CombineText[Combine Text]
    
    CombineText --> FormatOutput[Format Combined Output]
    FormatOutput --> SaveCombined[Save Combined Results]
    SaveCombined --> End
```

## Docker Deployment Flow

```mermaid
flowchart TD
    Start([Start Docker Deployment]) --> CheckDocker{Docker Installed?}
    
    CheckDocker -->|No| ErrorDocker[Error: Install Docker]
    CheckDocker -->|Yes| SelectMode{Select Mode}
    
    ErrorDocker --> End([End])
    
    SelectMode -->|CPU| BuildCPU[Build CPU Image]
    SelectMode -->|GPU| CheckNvidia{NVIDIA Docker?}
    
    CheckNvidia -->|No| ErrorNvidia[Error: Install NVIDIA Docker]
    CheckNvidia -->|Yes| BuildGPU[Build GPU Image]
    
    ErrorNvidia --> End
    
    BuildCPU --> CheckImageCPU{Image Exists?}
    BuildGPU --> CheckImageGPU{Image Exists?}
    
    CheckImageCPU -->|No| DockerBuildCPU[docker build CPU]
    CheckImageCPU -->|Yes| SkipBuildCPU[Skip Build]
    
    CheckImageGPU -->|No| DockerBuildGPU[docker build GPU]
    CheckImageGPU -->|Yes| SkipBuildGPU[Skip Build]
    
    DockerBuildCPU --> ImageReadyCPU[CPU Image Ready]
    SkipBuildCPU --> ImageReadyCPU
    
    DockerBuildGPU --> ImageReadyGPU[GPU Image Ready]
    SkipBuildGPU --> ImageReadyGPU
    
    ImageReadyCPU --> CreateVolumes[Create Volumes]
    ImageReadyGPU --> CreateVolumes
    
    CreateVolumes --> MountInput[Mount Input Directory]
    MountInput --> MountOutput[Mount Output Directory]
    MountOutput --> MountCache[Mount Model Cache]
    
    MountCache --> RunContainer[Run Container]
    RunContainer --> WaitStart[Wait for Startup]
    WaitStart --> HealthCheck{Health Check}
    
    HealthCheck -->|Fail| CheckRetry{Retry?}
    HealthCheck -->|Pass| ContainerReady[Container Ready]
    
    CheckRetry -->|Yes| WaitStart
    CheckRetry -->|No| ErrorStart[Startup Failed]
    
    ErrorStart --> ShowLogs[Show Container Logs]
    ShowLogs --> End
    
    ContainerReady --> DisplayURL[Display Access URL]
    DisplayURL --> End
```

## Kubernetes Deployment Flow

```mermaid
flowchart TD
    Start([Start K8s Deployment]) --> CheckKubectl{kubectl Available?}
    
    CheckKubectl -->|No| ErrorKubectl[Error: Install kubectl]
    CheckKubectl -->|Yes| CheckCluster{Cluster Connected?}
    
    ErrorKubectl --> End([End])
    
    CheckCluster -->|No| ErrorCluster[Error: Connect to Cluster]
    CheckCluster -->|Yes| CreateNamespace{Namespace Exists?}
    
    ErrorCluster --> End
    
    CreateNamespace -->|No| CreateNS[Create Namespace]
    CreateNamespace -->|Yes| UseExisting[Use Existing]
    
    CreateNS --> DeployPVC[Deploy PVCs]
    UseExisting --> DeployPVC
    
    DeployPVC --> WaitPVC{PVCs Bound?}
    
    WaitPVC -->|No| WaitPVCMore[Wait for PVCs]
    WaitPVC -->|Yes| DeployConfigMap[Deploy ConfigMap]
    
    WaitPVCMore --> WaitPVC
    
    DeployConfigMap --> SelectVersion{Select Version}
    
    SelectVersion -->|CPU| DeployCPU[Deploy CPU Deployment]
    SelectVersion -->|GPU| CheckGPUOperator{GPU Operator?}
    SelectVersion -->|Both| DeployBoth[Deploy Both]
    
    CheckGPUOperator -->|No| InstallGPUOp[Install GPU Operator]
    CheckGPUOperator -->|Yes| DeployGPU[Deploy GPU Deployment]
    
    InstallGPUOp --> WaitGPUOp[Wait for GPU Operator]
    WaitGPUOp --> DeployGPU
    
    DeployCPU --> WaitPodsCPU{Pods Ready?}
    DeployGPU --> WaitPodsGPU{Pods Ready?}
    DeployBoth --> WaitPodsBoth{All Pods Ready?}
    
    WaitPodsCPU -->|No| CheckPodsCPU[Check Pod Status]
    WaitPodsCPU -->|Yes| CreateServiceCPU[Create Service]
    
    WaitPodsGPU -->|No| CheckPodsGPU[Check Pod Status]
    WaitPodsGPU -->|Yes| CreateServiceGPU[Create Service]
    
    WaitPodsBoth -->|No| CheckPodsBoth[Check Pod Status]
    WaitPodsBoth -->|Yes| CreateServices[Create Services]
    
    CheckPodsCPU --> DescribePod[Describe Pod]
    CheckPodsGPU --> DescribePod
    CheckPodsBoth --> DescribePod
    
    DescribePod --> ShowLogs[Show Logs]
    ShowLogs --> FixIssue{Issue Fixed?}
    
    FixIssue -->|Yes| WaitPodsCPU
    FixIssue -->|No| ErrorDeploy[Deployment Failed]
    
    ErrorDeploy --> End
    
    CreateServiceCPU --> DeployIngress[Deploy Ingress]
    CreateServiceGPU --> DeployIngress
    CreateServices --> DeployIngress
    
    DeployIngress --> WaitIngress{Ingress Ready?}
    
    WaitIngress -->|No| WaitIngressMore[Wait for Ingress]
    WaitIngress -->|Yes| GetExternalIP[Get External IP]
    
    WaitIngressMore --> WaitIngress
    
    GetExternalIP --> DisplayAccess[Display Access Info]
    DisplayAccess --> VerifyHealth[Verify Health Checks]
    VerifyHealth --> DeploymentComplete[Deployment Complete]
    DeploymentComplete --> End
```

## Error Handling Flow

```mermaid
flowchart TD
    Start([Error Occurred]) --> CaptureError[Capture Error Details]
    
    CaptureError --> ClassifyError{Error Type}
    
    ClassifyError -->|Model Load| ModelError[Model Loading Error]
    ClassifyError -->|Processing| ProcessError[Processing Error]
    ClassifyError -->|File I/O| FileError[File I/O Error]
    ClassifyError -->|Memory| MemoryError[Out of Memory]
    ClassifyError -->|GPU| GPUError[GPU Error]
    ClassifyError -->|Network| NetworkError[Network Error]
    
    ModelError --> CheckModelExists{Model Exists?}
    CheckModelExists -->|No| DownloadModel[Download Model]
    CheckModelExists -->|Yes| CheckModelCorrupt{Model Corrupt?}
    
    DownloadModel --> RetryLoad[Retry Load]
    CheckModelCorrupt -->|Yes| RedownloadModel[Re-download Model]
    CheckModelCorrupt -->|No| CheckMemory[Check Memory]
    
    RedownloadModel --> RetryLoad
    
    ProcessError --> LogProcessError[Log Processing Error]
    LogProcessError --> CheckRetryable{Retryable?}
    
    CheckRetryable -->|Yes| RetryProcess[Retry Processing]
    CheckRetryable -->|No| SkipImage[Skip Image]
    
    RetryProcess --> CheckRetryCount{Retry Count < 3?}
    CheckRetryCount -->|Yes| ProcessError
    CheckRetryCount -->|No| SkipImage
    
    FileError --> CheckPermissions{Permissions OK?}
    CheckPermissions -->|No| FixPermissions[Fix Permissions]
    CheckPermissions -->|Yes| CheckDiskSpace{Disk Space?}
    
    FixPermissions --> RetryFile[Retry File Operation]
    CheckDiskSpace -->|Low| CleanupSpace[Cleanup Space]
    CheckDiskSpace -->|OK| CheckPath[Check Path]
    
    CleanupSpace --> RetryFile
    CheckPath --> RetryFile
    
    MemoryError --> CheckDevice{Using GPU?}
    CheckDevice -->|Yes| SwitchCPU[Switch to CPU]
    CheckDevice -->|No| ReduceBatch[Reduce Batch Size]
    
    SwitchCPU --> RetryProcess
    ReduceBatch --> RetryProcess
    
    GPUError --> CheckGPUAvailable{GPU Available?}
    CheckGPUAvailable -->|No| FallbackCPU[Fallback to CPU]
    CheckGPUAvailable -->|Yes| ResetGPU[Reset GPU]
    
    FallbackCPU --> RetryProcess
    ResetGPU --> RetryProcess
    
    NetworkError --> CheckConnection{Connection OK?}
    CheckConnection -->|No| WaitRetry[Wait and Retry]
    CheckConnection -->|Yes| CheckProxy[Check Proxy]
    
    WaitRetry --> RetryNetwork[Retry Network]
    CheckProxy --> RetryNetwork
    
    RetryLoad --> Success{Success?}
    RetryProcess --> Success
    RetryFile --> Success
    RetryNetwork --> Success
    SkipImage --> LogSkip[Log Skipped Image]
    
    Success -->|Yes| Continue[Continue Processing]
    Success -->|No| FinalError[Final Error]
    
    LogSkip --> Continue
    
    Continue --> End([End])
    
    FinalError --> NotifyUser[Notify User]
    NotifyUser --> SaveErrorLog[Save Error Log]
    SaveErrorLog --> End
```

## System Health Monitoring Flow

```mermaid
flowchart TD
    Start([Start Monitoring]) --> InitMetrics[Initialize Metrics]
    
    InitMetrics --> MonitorLoop{Monitoring Active?}
    
    MonitorLoop -->|No| End([End])
    MonitorLoop -->|Yes| CollectMetrics[Collect Metrics]
    
    CollectMetrics --> CheckCPU[Check CPU Usage]
    CheckCPU --> CheckMemory[Check Memory Usage]
    CheckMemory --> CheckGPU[Check GPU Usage]
    CheckGPU --> CheckDisk[Check Disk Space]
    CheckDisk --> CheckNetwork[Check Network]
    
    CheckNetwork --> AnalyzeMetrics{Metrics OK?}
    
    AnalyzeMetrics -->|All OK| LogNormal[Log Normal Status]
    AnalyzeMetrics -->|Warning| LogWarning[Log Warning]
    AnalyzeMetrics -->|Critical| LogCritical[Log Critical]
    
    LogWarning --> SendAlert[Send Alert]
    LogCritical --> SendAlert
    
    SendAlert --> TakeAction{Auto-Remediate?}
    
    TakeAction -->|Yes| Remediate[Take Remediation Action]
    TakeAction -->|No| NotifyAdmin[Notify Administrator]
    
    Remediate --> CheckFixed{Issue Fixed?}
    
    CheckFixed -->|Yes| LogResolved[Log Resolution]
    CheckFixed -->|No| NotifyAdmin
    
    LogNormal --> Wait[Wait Interval]
    LogResolved --> Wait
    NotifyAdmin --> Wait
    
    Wait --> MonitorLoop
```

---

**Note**: These flowcharts provide a comprehensive view of the GutenOCR application's operation. They can be rendered using any Mermaid-compatible viewer or documentation platform.