import { useEffect } from 'react'

export function useRevealOnScroll() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible')
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.18 },
    )

    const observeRevealElements = (root: ParentNode = document) => {
      const elements = root.querySelectorAll<HTMLElement>('[data-reveal]')
      elements.forEach((element) => {
        if (!element.classList.contains('is-visible')) {
          observer.observe(element)
        }
      })
    }

    observeRevealElements()

    const mutationObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (!(node instanceof HTMLElement)) {
            return
          }

          if (node.matches('[data-reveal]')) {
            observeRevealElements(node.parentElement ?? document)
            return
          }

          observeRevealElements(node)
        })
      })
    })

    mutationObserver.observe(document.body, {
      childList: true,
      subtree: true,
    })

    return () => {
      observer.disconnect()
      mutationObserver.disconnect()
    }
  }, [])
}
