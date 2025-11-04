{ lib
, python3
}:

python3.pkgs.buildPythonApplication {
  pname = "redhat_iso";
  version = "1.0.0";

  pyproject = true;

  src = ./.;

  build-system = with python3.pkgs; [
    setuptools
  ];

  propagatedBuildInputs = with python3.pkgs; [
    requests
  ];

  # No tests yet
  doCheck = false;

  meta = with lib; {
    description = "Red Hat ISO Download Tool - List and download Red Hat ISO files";
    homepage = "https://github.com/yourusername/download-redhat-iso-files";
    license = licenses.mit;
    maintainers = [ ];
  };
}
