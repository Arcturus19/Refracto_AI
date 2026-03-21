# Eye Hospital Device Research And Local Deployment Plan

## Objective

Deploy Refracto AI in eye hospitals where fundus cameras and OCT systems commonly run on Windows-based acquisition workstations and export studies as DICOM. The target workflow is:

1. The imaging device acquires a fundus or OCT study.
2. The device sends the study as DICOM to Refracto AI.
3. Refracto AI ingests the study, links it to a patient, preprocesses the image, runs analysis, and returns results locally.

## Executive Summary

Modern ophthalmology imaging environments are usually built around vendor-managed Windows workstations, especially for retina, fundus, OCT, and multimodal imaging systems. In practice, hospitals do not usually want third-party software deeply modifying the vendor acquisition stack unless the vendor explicitly supports it. Because of that, the safest deployment model is usually not "install the full product directly inside the camera software workstation" but rather one of these two patterns:

1. Install a lightweight local Refracto AI gateway on the same Windows machine only if vendor policy allows it.
2. Prefer a sidecar Windows mini-PC or hospital-owned workstation on the same subnet, configured as a DICOM receiver, while the imaging device keeps using its native software unchanged.

For this repository, the second pattern is the safer first production target.

## Representative Device Landscape

This is a practical shortlist of current device classes and representative systems commonly seen in retina and eye hospital workflows. Procurement varies by region and hospital, so treat this as a targeting list rather than an exhaustive market inventory.

### Combined OCT + Fundus / Multimodal Platforms

- Heidelberg Engineering SPECTRALIS: multimodal retinal imaging platform combining confocal scanning laser ophthalmoscopy with SD-OCT.
- ZEISS CIRRUS family: OCT-focused retina platform widely used in ophthalmology clinics and hospitals.
- Topcon Maestro2 / Triton family: combined retinal camera and OCT workflow platforms.
- NIDEK OCT and multimodal retina platforms: commonly deployed in ophthalmic imaging settings.

These are the highest-value integration targets because they are already part of specialist retinal workflows and often support network-based export and DICOM connectivity through device or review-station software.

### Fundus Cameras

- Canon CR-series fundus cameras.
- Topcon TRC and NW-series fundus cameras.
- NIDEK AFC-series non-mydriatic fundus cameras.
- Optomed Aurora portable fundus camera.

These are simpler integration targets than OCT volumes because they usually send single 2D images or smaller studies.

### Ultra-Widefield / Specialty Retina Imaging

- Optos systems such as Daytona, California, and Monaco.
- ZEISS CLARUS widefield imaging systems.

These can be important in retina hospitals, but they sometimes have more vendor-specific workflow layers, which can make DICOM integration more dependent on the exact installed software package.

## What Is Consistent Across Most Newer Devices

Across newer ophthalmic imaging systems, these patterns are common:

- The device is controlled by a Windows workstation or review station.
- The vendor application manages acquisition, patient lookup, and export.
- DICOM support exists, but the exact level varies by license and model.
- Hospitals often configure the device to send to a PACS, archive, or DICOM node using AE Title, IP, and port.
- Some devices send native ophthalmic DICOM objects, while others may send Secondary Capture, JPEG export, or vendor-specific derivatives depending on configuration.

## Integration-Relevant DICOM Objects

For ophthalmology, the relevant DICOM objects are not limited to generic modality tags like OP and OPT. The ecosystem also includes ophthalmic-specific SOP Classes such as:

- Ophthalmic Photography 8-bit and 16-bit Image Storage.
- Ophthalmic Tomography Image Storage.
- Ophthalmic OCT En Face Image Storage.
- Ophthalmic OCT B-scan Volume Analysis Storage.
- Macular Grid Thickness and Volume Report.
- Ophthalmic Thickness Map Storage.
- Secondary Capture Image Storage.

This matters because a real production deployment must validate not only that a device "sends DICOM", but exactly which SOP Classes it sends and whether pixel data is directly usable by the inference pipeline.

## What This Repository Already Supports

The current codebase already contains a workable ingestion foundation:

- A DICOM Store SCP implemented with pynetdicom that listens for incoming DICOM C-STORE and C-ECHO.
- Auto-ingestion logic that can find or create patients and upload files into the imaging service.
- Imaging service support for DICOM uploads.
- DICOM-to-PNG conversion inside the imaging service before storage.
- Separate ML endpoints for fundus and OCT image analysis.

Current strengths:

- The DICOM receiver supports all storage presentation contexts.
- The architecture is already microservice-oriented, which helps isolate acquisition, storage, and inference concerns.
- The DICOM service can run as a plain Python service, so it is not inherently Docker-only.

## Current Gaps And Risks In This Repository

### 1. OCT Modality Routing Needs Correction

In the DICOM service, `OPT` is currently treated as `FUNDUS`. That is not correct for ophthalmic tomography and will misroute OCT studies in downstream processing.

### 2. The ML Service Does Not Accept DICOM Directly

The ML service validates raster images through PIL and expects standard image bytes. That means DICOM must be converted before inference, which is fine, but only if the conversion preserves the clinically relevant OCT or fundus representation.

### 3. OCT Conversion Is Too Simplistic For Production

The current imaging service converts DICOM by reading pixel data and often taking the first frame if the image is multi-frame. That is acceptable for a prototype but too weak for many OCT studies, where the clinically useful representation may be:

- a selected B-scan,
- an en-face rendering,
- a thickness map,
- a report object,
- or a vendor-generated derived image rather than raw volume pixels.

### 4. Full On-Machine Deployment Is Not Yet Operationally Hardened

The backend is currently documented primarily around Docker Compose. That is good for development and for hospital-owned Windows PCs with Docker Desktop, but it is not yet packaged as a reliable Windows service stack for restricted clinical workstations.

### 5. Hospital Security Controls Are Not Yet Fully Enforced

Clinical deployment will require:

- AE Title allowlists.
- IP allowlists.
- audit logging,
- protected local storage,
- service recovery,
- and ideally TLS or network isolation.

Some of this is described in the documentation, but not fully hardened as a deployment product.

## Recommended Deployment Architecture

### Preferred Architecture: Local Sidecar Gateway

This should be the default target for hospitals.

1. Keep the imaging device and its vendor Windows software unchanged.
2. Place a hospital-owned Windows PC or mini-server on the same VLAN/subnet.
3. Run Refracto AI DICOM receiver and local backend services there.
4. Configure each camera or OCT machine to send DICOM to the Refracto AI node.
5. Return results over the local web UI or through a workstation browser.

Benefits:

- avoids modifying vendor acquisition software,
- reduces risk to OEM support contracts,
- simplifies rollback,
- allows centralized logs and backups,
- and still keeps the workflow fully local inside the hospital network.

### Secondary Architecture: Direct Install On The Device Workstation

Use this only when all of the following are true:

- the hospital owns the workstation administratively,
- the vendor allows third-party software,
- the device software remains stable under load,
- and local firewall, antivirus, and Windows policy exceptions can be managed.

This model is possible, but it carries more operational risk.

## Recommended First Production Scope

Do not try to support every ophthalmic DICOM object on day one.

Target this first:

1. Fundus DICOM or fundus export from one camera family.
2. OCT export from one device family that sends a stable 2D derived image or B-scan representation.
3. One site pilot with one hospital network and one vendor workflow.

The fastest path is usually:

- one fundus camera integration,
- one OCT integration,
- one hospital pilot,
- one local deployment pattern.

## Deployment Plan

### Phase 0: Device Discovery And Conformance Collection

Goal: identify the exact imaging systems and software versions in the target hospitals.

Tasks:

1. Make an inventory per site:
   - vendor,
   - model,
   - software version,
   - Windows version,
   - DICOM license status,
   - export options,
   - and whether the device sends directly or only through a review station.
2. Request the DICOM conformance statement from each vendor or local distributor.
3. Verify which SOP Classes are actually transmitted.
4. Determine whether the device can send automatically after acquisition or only by manual export.

Deliverable:

- A device matrix for each site.

### Phase 1: Repository Hardening For Real Ophthalmic DICOM

Goal: make the current stack reliable for actual hospital studies.

Required engineering changes:

1. Fix modality-to-image-type mapping in the DICOM service so OCT is not treated as fundus.
2. Add SOP Class based routing rather than relying only on `Modality`.
3. Persist DICOM metadata needed for debugging and audit:
   - SOP Class UID,
   - Transfer Syntax UID,
   - Manufacturer,
   - Model Name,
   - Series Description,
   - Number of Frames,
   - Rows and Columns.
4. Improve DICOM preprocessing for OCT:
   - identify multi-frame studies,
   - choose the correct derived frame or representative B-scan,
   - preserve important orientation/context,
   - and keep original DICOM alongside derived PNG.
5. Add a background analysis trigger after imaging upload completes.
6. Store the analysis result linked to the original study and derived image.

Deliverable:

- A pilot-ready DICOM ingest and inference path.

### Phase 2: Windows Local Deployment Packaging

Goal: run the project reliably on a Windows hospital workstation.

Recommended packaging options:

1. Docker Desktop deployment for hospital-owned Windows PCs where Docker is allowed.
2. Native Windows services for the DICOM receiver and APIs if Docker is not allowed.
3. Optional local PostgreSQL and local object storage, or a simplified single-node storage path for pilot use.

Windows deployment requirements:

- auto-start on boot,
- service restart on failure,
- log rotation,
- local firewall rules for DICOM port,
- fixed local IP or DNS name,
- and installation scripts suitable for IT administrators.

Deliverable:

- A repeatable Windows installation package and runbook.

### Phase 3: Hospital Pilot

Goal: validate real-world interoperability.

Tasks:

1. Configure one fundus camera and one OCT device to send to Refracto AI.
2. Run C-ECHO and test C-STORE with non-production sample studies.
3. Validate patient matching and study association.
4. Confirm image preprocessing quality with an ophthalmologist.
5. Measure end-to-end turnaround time from acquisition to AI result.
6. Validate failure handling when the network, storage, or downstream service is unavailable.

Success criteria:

- reliable study receipt,
- correct modality classification,
- clinically acceptable derived image selection,
- stable local inference,
- and recoverable error handling.

### Phase 4: Production Hardening

Goal: move from pilot to repeatable hospital deployment.

Tasks:

1. Add AE Title and IP allowlists.
2. Add PHI-safe logging and audit trails.
3. Encrypt or otherwise protect local storage.
4. Add retention and cleanup policies.
5. Define backup and recovery procedures.
6. Add site monitoring and health dashboards.
7. Document change control for hospital IT.

Deliverable:

- A deployable local product for controlled hospital rollout.

## Site Survey Checklist

Before any installation, collect these answers from the hospital:

- What exact fundus and OCT models are installed?
- What Windows version is on each workstation?
- Are the devices domain-joined or vendor-locked?
- Is third-party software allowed on the acquisition PC?
- Is Docker allowed?
- Is DICOM enabled and licensed?
- Can the device send automatically to an external DICOM node?
- Is there a review station separate from the acquisition PC?
- What subnet, firewall rules, and IP reservations are available?
- Does the hospital want all processing to stay fully on-premise?

## Practical Recommendation For Your Project

For your first implementation, do this:

1. Choose one hospital.
2. Choose one fundus machine and one OCT machine.
3. Obtain real sample DICOMs from those exact devices.
4. Fix the repository’s OCT routing and SOP Class handling.
5. Package the DICOM receiver plus backend for a local Windows sidecar machine.
6. Validate with ophthalmologists that the derived OCT image sent into ML is clinically meaningful.

This is a much stronger approach than trying to claim compatibility with every fundus and OCT device up front.

## Immediate Next Engineering Actions In This Repo

1. Correct OCT mapping in the DICOM service.
2. Add SOP Class aware ophthalmic routing.
3. Store original DICOM plus derived image and metadata.
4. Add a post-upload analysis workflow.
5. Create a Windows deployment mode and installation guide.
6. Test against real ophthalmic DICOM files from at least one vendor fundus device and one vendor OCT device.

## Final Recommendation

Yes, this project can be adapted for local deployment in eye hospitals that use Windows-based fundus and OCT systems with DICOM export. But the technically correct product target is not just "install on the machine". The real target is:

- local hospital deployment,
- DICOM interoperability with ophthalmic devices,
- and a deployment pattern that respects vendor workstation constraints.

For production, the safest first path is a local Refracto AI DICOM gateway on a hospital-owned Windows sidecar machine, not a deep direct install into every vendor acquisition workstation.