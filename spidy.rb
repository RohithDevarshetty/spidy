class Spidy < Formula
  include Language::Python::Virtualenv

  desc "Terminal-based Spiderman swinging game with amazing ASCII graphics"
  homepage "https://github.com/RohithDevarshetty/spidy"
  url "https://github.com/RohithDevarshetty/spidy/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256"
  license "MIT"

  depends_on "python@3.11"

  def install
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      🕷️  Welcome to Spidy - The Spiderman Swinging Game! 🕷️

      To start playing, simply run:
        spidy

      Controls:
        SPACE - Shoot web and swing
        Q     - Quit game

      Swing through the city, avoid obstacles, and rack up points!

      Note: For the best experience, maximize your terminal window.
    EOS
  end

  test do
    system "#{bin}/spidy", "--version"
  end
end
