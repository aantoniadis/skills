import { dirname, join } from "node:path"
import { realpathSync } from "node:fs"
import { fileURLToPath } from "node:url"

const root = dirname(dirname(realpathSync(fileURLToPath(import.meta.url))))

export const Skills = async () => ({
  config: async (config) => {
    const dir = join(root, "skills")
    config.skills ??= {}
    config.skills.paths ??= []
    if (!config.skills.paths.includes(dir)) config.skills.paths.push(dir)
  },
})
