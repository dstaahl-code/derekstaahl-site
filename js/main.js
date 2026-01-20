/**
 * Derek Staahl Portfolio - Main JavaScript
 * Handles: Mobile navigation toggle, scroll fade-in animations
 */

(function() {
  'use strict';

  // ==========================================================================
  // Mobile Navigation
  // ==========================================================================

  const navToggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.nav');
  const navOverlay = document.querySelector('.nav-overlay');

  if (navToggle && nav) {
    // Toggle navigation on button click
    navToggle.addEventListener('click', function() {
      const isExpanded = navToggle.getAttribute('aria-expanded') === 'true';
      navToggle.setAttribute('aria-expanded', !isExpanded);
      nav.classList.toggle('nav--open');

      if (navOverlay) {
        navOverlay.classList.toggle('nav-overlay--visible');
      }

      // Prevent body scroll when nav is open
      document.body.style.overflow = isExpanded ? '' : 'hidden';
    });

    // Close navigation when overlay is clicked
    if (navOverlay) {
      navOverlay.addEventListener('click', function() {
        navToggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('nav--open');
        navOverlay.classList.remove('nav-overlay--visible');
        document.body.style.overflow = '';
      });
    }

    // Close navigation on Escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && nav.classList.contains('nav--open')) {
        navToggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('nav--open');
        if (navOverlay) {
          navOverlay.classList.remove('nav-overlay--visible');
        }
        document.body.style.overflow = '';
        navToggle.focus();
      }
    });

    // Close navigation when a link is clicked (for single-page sections)
    const navLinks = nav.querySelectorAll('.nav__link');
    navLinks.forEach(function(link) {
      link.addEventListener('click', function() {
        if (window.innerWidth < 768) {
          navToggle.setAttribute('aria-expanded', 'false');
          nav.classList.remove('nav--open');
          if (navOverlay) {
            navOverlay.classList.remove('nav-overlay--visible');
          }
          document.body.style.overflow = '';
        }
      });
    });
  }

  // ==========================================================================
  // Scroll Fade-In Animation (Intersection Observer)
  // ==========================================================================

  // Check if user prefers reduced motion
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!prefersReducedMotion) {
    const fadeElements = document.querySelectorAll('.fade-in');

    if (fadeElements.length > 0 && 'IntersectionObserver' in window) {
      const observerOptions = {
        root: null,
        rootMargin: '0px 0px -50px 0px',
        threshold: 0.1
      };

      const fadeObserver = new IntersectionObserver(function(entries, observer) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('fade-in--visible');
            observer.unobserve(entry.target);
          }
        });
      }, observerOptions);

      fadeElements.forEach(function(element) {
        fadeObserver.observe(element);
      });
    } else {
      // Fallback: Show all elements if IntersectionObserver is not supported
      fadeElements.forEach(function(element) {
        element.classList.add('fade-in--visible');
      });
    }
  } else {
    // If user prefers reduced motion, show all elements immediately
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach(function(element) {
      element.classList.add('fade-in--visible');
    });
  }

  // ==========================================================================
  // Contact Success Message
  // ==========================================================================

  const params = new URLSearchParams(window.location.search);
  if (params.get('success') === 'true') {
    const successBanner = document.querySelector('.form-success');
    if (successBanner) {
      successBanner.hidden = false;
      successBanner.scrollIntoView({ block: 'center' });
    }
  }

})();
