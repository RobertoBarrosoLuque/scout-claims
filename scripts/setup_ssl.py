import subprocess
from pathlib import Path


def check_openssl():
    """Check if OpenSSL is available."""
    try:
        subprocess.run(["openssl", "version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def generate_ssl_certificates():
    """Generate self-signed SSL certificates for local development."""
    cert_dir = Path("")
    key_file = cert_dir / "key.pem"
    cert_file = cert_dir / "cert.pem"

    # Check if certificates already exist
    if key_file.exists() and cert_file.exists():
        print("✅ SSL certificates already exist!")
        return True

    if not check_openssl():
        print("❌ OpenSSL not found. Please install OpenSSL first.")
        print("On Ubuntu/Debian: sudo apt-get install openssl")
        print("On macOS: brew install openssl")
        print(
            "On Windows: Download from https://slproweb.com/products/Win32OpenSSL.html"
        )
        return False

    print("🔐 Generating self-signed SSL certificates...")

    # Generate private key
    key_cmd = ["openssl", "genrsa", "-out", str(key_file), "2048"]

    # Generate certificate
    cert_cmd = [
        "openssl",
        "req",
        "-new",
        "-x509",
        "-key",
        str(key_file),
        "-out",
        str(cert_file),
        "-days",
        "365",
        "-subj",
        "/C=US/ST=CA/L=Local/O=Dev/CN=localhost",
    ]

    try:
        subprocess.run(key_cmd, check=True)
        subprocess.run(cert_cmd, check=True)
        print("✅ SSL certificates generated successfully!")
        print(f"   Private key: {key_file}")
        print(f"   Certificate: {cert_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate SSL certificates: {e}")
        return False


def main():
    """Main function to set up SSL certificates."""
    print("🚀 Setting up SSL certificates for local HTTPS...")

    if generate_ssl_certificates():
        print("\n📋 Next steps:")
        print("1. Run your Gradio app with the generated certificates")
        print("2. Open https://localhost:7860 in your browser")
        print(
            "3. Accept the security warning (click 'Advanced' → 'Proceed to localhost')"
        )
        print("4. Allow microphone access when prompted")
        print(
            "\n⚠️  Note: You'll see a security warning because these are self-signed certificates."
        )
        print(
            "   This is normal for local development - just click through the warning."
        )
    else:
        print("\n❌ SSL setup failed. Alternative options:")
        print(
            "1. Use Chrome with: --unsafely-treat-insecure-origin-as-secure=http://localhost:7860"
        )
        print(
            "2. Use Firefox and set media.devices.insecure.enabled=true in about:config"
        )
        print("3. Deploy to a server with proper SSL certificates")


if __name__ == "__main__":
    main()
