{
  lib,
  buildPythonPackage,

  hatchling,
  click,
  protobuf,
  rich,
}:

buildPythonPackage {
  pname = "vector2mcap";
  version = "0.1.0";
  pyproject = true;

  src = ./.;

  build-system = [
    hatchling
  ];

  dependencies = [
    click
    protobuf
    rich
  ];

  # Disable runtime dependency checks since we have version mismatches
  dontCheckRuntimeDeps = true;
  doCheck = false;

  pythonImportsCheck = [
    "vector2mcap"
  ];

  meta = with lib; {
    description = "Convert Vector JSONL telemetry files to MCAP format using protobuf serialization";
    homepage = "https://github.com/noahbresler/vector2mcap";
    license = licenses.mit; # Adjust if different
    maintainers = [ ];
    mainProgram = "vector2mcap";
  };
}
