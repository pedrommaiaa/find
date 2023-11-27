#!/usr/bin/env python3
import sys
import asyncio
from jet.jet import Jet

if __name__ == "__main__":
    jet = Jet()
    asyncio.run(jet.run())
