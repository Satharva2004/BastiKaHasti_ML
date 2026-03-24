import { useState } from 'react'

const LEFT_HAND_ASSET = '/hero-hand-left.png'
const RIGHT_HAND_ASSET = '/hero-hand-right.png'

type HandSlotProps = {
  side: 'left' | 'right'
  assetSrc: string
}

function HandSlot({ side, assetSrc }: HandSlotProps) {
  const [isMissing, setIsMissing] = useState(false)

  if (assetSrc && !isMissing) {
    return (
      <img
        src={assetSrc}
        alt=""
        aria-hidden="true"
        className={`hero__hand hero__hand--${side}`}
        onError={() => setIsMissing(true)}
      />
    )
  }

  return (
    <div
      aria-hidden="true"
      className={`hero__hand hero__hand--${side} hero__hand--placeholder`}
    >
      <span>{side === 'left' ? 'LEFT HAND ASSET' : 'RIGHT HAND ASSET'}</span>
    </div>
  )
}

export function HeroHands() {
  return (
    <>
      <HandSlot side="left" assetSrc={LEFT_HAND_ASSET} />
      <HandSlot side="right" assetSrc={RIGHT_HAND_ASSET} />
    </>
  )
}
