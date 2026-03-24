(function () {
  let bootstrapPromise = null;
  let revealObserver = null;

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function todayISO() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function parseISODate(value) {
    const [year, month, day] = String(value).split("-").map(Number);
    return new Date(year, month - 1, day);
  }

  function formatDate(value) {
    if (!value) {
      return "Not selected";
    }

    return new Intl.DateTimeFormat("en-IN", {
      weekday: "short",
      day: "numeric",
      month: "short",
      year: "numeric",
    }).format(parseISODate(value));
  }

  function formatDateTime(value) {
    if (!value) {
      return "";
    }

    return new Intl.DateTimeFormat("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(value));
  }

  function getInitials(name) {
    return String(name || "")
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join("");
  }

  async function request(path, options = {}) {
    const config = {
      ...options,
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {}),
      },
    };

    if (config.body && typeof config.body !== "string") {
      config.body = JSON.stringify(config.body);
    }

    const response = await fetch(path, config);
    const contentType = response.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");
    const payload = response.status === 204
      ? null
      : isJson
        ? await response.json()
        : await response.text();

    if (!response.ok) {
      throw new Error(payload && payload.error ? payload.error : "Request failed.");
    }

    return payload;
  }

  function loadBootstrap() {
    if (!bootstrapPromise) {
      bootstrapPromise = request("/api/bootstrap");
    }

    return bootstrapPromise;
  }

  function renderShell() {
    const headerMount = document.querySelector("[data-site-header]");
    const footerMount = document.querySelector("[data-site-footer]");
    const currentPage = document.body.dataset.page;

    if (headerMount) {
      headerMount.innerHTML = `
        <header class="site-header">
          <div class="page-shell header-inner">
            <a class="brand" href="/index.html">
              <span class="brand-mark">M</span>
              <span>MediSlot</span>
            </a>
            <button
              class="nav-toggle"
              type="button"
              aria-expanded="false"
              aria-controls="site-nav"
            >
              Menu
            </button>
            <nav class="site-nav" id="site-nav">
              <a data-page="home" href="/index.html">Home</a>
              <a data-page="doctors" href="/doctors.html">Doctors</a>
              <a data-page="book" href="/book.html">Book Appointment</a>
              <a data-page="locations" href="/locations.html">Locations</a>
              <a data-page="contact" href="/contact.html">Contact</a>
            </nav>
          </div>
        </header>
      `;
    }

    if (footerMount) {
      footerMount.innerHTML = `
        <footer class="site-footer">
          <div class="page-shell footer-inner">
            <div>
              <a class="brand" href="/index.html">
                <span class="brand-mark">M</span>
                <span>MediSlot</span>
              </a>
              <p class="footer-copy">
                Responsive doctor appointment booking for patients, clinics, and
                administrators.
              </p>
            </div>
            <div class="footer-links">
              <a href="/doctors.html">Doctors</a>
              <a href="/book.html">Book Appointment</a>
              <a href="/locations.html">Locations</a>
              <a href="/contact.html">Contact</a>
              <a data-admin-link href="/login.html">Admin Login</a>
            </div>
          </div>
        </footer>
      `;
    }

    const nav = document.getElementById("site-nav");
    const toggle = document.querySelector(".nav-toggle");

    document.querySelectorAll(".site-nav a").forEach((link) => {
      if (link.dataset.page === currentPage) {
        link.classList.add("is-active");
        link.setAttribute("aria-current", "page");
      }

      link.addEventListener("click", () => {
        nav?.classList.remove("is-open");
        toggle?.setAttribute("aria-expanded", "false");
      });
    });

    toggle?.addEventListener("click", () => {
      const open = nav?.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(Boolean(open)));
    });
  }

  async function hydrateAdminLink() {
    const adminLink = document.querySelector("[data-admin-link]");

    if (!adminLink) {
      return;
    }

    try {
      const session = await request("/api/admin/session");

      if (session.authenticated) {
        adminLink.href = "/admin.html";
        adminLink.textContent = "Admin View";
        return;
      }
    } catch (error) {
      console.error(error);
    }

    adminLink.href = "/login.html";
    adminLink.textContent = "Admin Login";
  }

  function bindReveal(scope = document) {
    const items = scope.querySelectorAll(".reveal:not([data-reveal-bound])");

    if (!items.length) {
      return;
    }

    if (!("IntersectionObserver" in window)) {
      items.forEach((item) => {
        item.classList.add("is-visible");
        item.dataset.revealBound = "true";
      });
      return;
    }

    if (!revealObserver) {
      revealObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              revealObserver.unobserve(entry.target);
            }
          });
        },
        {
          threshold: 0.18,
        }
      );
    }

    items.forEach((item) => {
      item.dataset.revealBound = "true";
      revealObserver.observe(item);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    renderShell();
    bindReveal(document);
    hydrateAdminLink();
  });

  window.MediSlot = {
    escapeHtml,
    todayISO,
    formatDate,
    formatDateTime,
    getInitials,
    request,
    loadBootstrap,
    bindReveal,
    hydrateAdminLink,
  };
})();
