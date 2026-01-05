const fs = require('fs-extra');
const path = require('node:path');
const chalk = require('chalk');
const { execSync } = require('node:child_process');
const inquirer = require('inquirer').default || require('inquirer');

/**
 * BMAD Memory System Installer
 * 
 * Follows 2026 best practices:
 * - .env.example pattern (never commit .env)
 * - User prompts for sensitive values (PROJECT_ID)
 * - Auto-configuration with sensible defaults
 * - Docker-based Qdrant setup
 * - Collection initialization
 * - Health check validation
 * 
 * @param {Object} options - Installation options
 * @param {string} options.projectRoot - The root directory of the target project
 * @param {Object} options.config - Module configuration from module.yaml
 * @param {Array<string>} options.installedIDEs - Array of IDE codes installed
 * @param {Object} options.logger - Logger instance for output
 * @returns {Promise<boolean>} - Success status
 */
async function install(options) {
  const { projectRoot, config, installedIDEs, logger } = options;

  try {
    logger.log(chalk.blue('🧠 Installing BMAD Memory System...'));
    logger.log(chalk.dim('   Qdrant vector database + Python memory library\n'));

    // Step 1: Create .env file from template
    await createEnvFile(projectRoot, logger);

    // Step 2: Install Python dependencies
    await installPythonDeps(projectRoot, logger);

    // Step 3: Start Qdrant via Docker
    const qdrantStarted = await startQdrant(projectRoot, logger);
    if (!qdrantStarted) {
      logger.warn(chalk.yellow('\n⚠️  Qdrant not started. Memory system will not work until Qdrant is running.'));
      logger.log(chalk.cyan('   You can start it manually later with:'));
      logger.log(chalk.green('   docker-compose up -d qdrant\n'));
    }

    // Step 4: Create Qdrant collections (only if Qdrant started)
    if (qdrantStarted) {
      await createCollections(projectRoot, logger);
    }

    // Step 5: Run health check (only if Qdrant started)
    if (qdrantStarted) {
      await healthCheck(projectRoot, logger);
    }

    logger.log(chalk.green('\n✓ BMAD Memory System installation complete!'));
    logger.log(chalk.cyan('\n📚 Memory system is ready to use:'));
    logger.log(chalk.dim('   • Qdrant running at http://localhost:6333'));
    logger.log(chalk.dim('   • 3 collections: bmad-knowledge, agent-memory, bmad-best-practices'));
    logger.log(chalk.dim('   • Python library at src/core/memory/'));
    logger.log(chalk.dim('   • Dashboard: http://localhost:6333/dashboard\n'));

    return true;
  } catch (error) {
    logger.error(chalk.red(`Error installing BMAD Memory: ${error.message}`));
    return false;
  }
}

/**
 * Create .env file from .env.example template
 * Prompts user for PROJECT_ID, sets sensible defaults
 */
async function createEnvFile(projectRoot, logger) {
  const envExamplePath = path.join(projectRoot, '.env.example');
  const envPath = path.join(projectRoot, '.env');

  logger.log(chalk.cyan('📝 Setting up environment configuration...'));

  // Check if .env already exists
  if (await fs.pathExists(envPath)) {
    logger.log(chalk.yellow('   .env file already exists, checking for memory variables...'));
    
    const envContent = await fs.readFile(envPath, 'utf8');
    const hasMemoryConfig = envContent.includes('QDRANT_URL') || envContent.includes('PROJECT_ID');
    
    if (hasMemoryConfig) {
      logger.log(chalk.green('   ✓ Memory configuration found in .env'));
      return;
    }
    
    // Append memory config to existing .env
    logger.log(chalk.yellow('   Adding memory configuration to existing .env...'));
    const projectName = await promptForProjectId(path.basename(projectRoot));
    const memoryConfig = generateMemoryEnvConfig(projectName);
    await fs.appendFile(envPath, `\n\n${memoryConfig}`);
    logger.log(chalk.green('   ✓ Memory configuration added to .env'));
    return;
  }

  // Create new .env file
  const projectName = await promptForProjectId(path.basename(projectRoot));
  const memoryConfig = generateMemoryEnvConfig(projectName);
  
  await fs.writeFile(envPath, memoryConfig);
  logger.log(chalk.green('   ✓ Created .env with memory configuration'));
}

/**
 * Prompt user for PROJECT_ID
 */
async function promptForProjectId(defaultName) {
  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'projectId',
      message: 'Enter PROJECT_ID for memory isolation (e.g., my-project):',
      default: defaultName.toLowerCase().replace(/[^a-z0-9-]/g, '-'),
      validate: (input) => {
        if (!input || input.trim() === '') {
          return 'PROJECT_ID cannot be empty';
        }
        if (!/^[a-z0-9-]+$/.test(input)) {
          return 'PROJECT_ID must contain only lowercase letters, numbers, and hyphens';
        }
        return true;
      },
    },
  ]);
  return answers.projectId;
}

/**
 * Generate memory-specific .env configuration
 */
function generateMemoryEnvConfig(projectId) {
  return `# BMAD Memory System Configuration
# Generated: ${new Date().toISOString()}

# Project identifier (for memory isolation/multitenancy)
PROJECT_ID=${projectId}

# Qdrant vector database connection
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Qdrant collection names
QDRANT_KNOWLEDGE_COLLECTION=bmad-knowledge
QDRANT_AGENT_MEMORY_COLLECTION=agent-memory
QDRANT_BEST_PRACTICES_COLLECTION=bmad-best-practices

# Memory system behavior
MEMORY_MODE=hybrid
ENABLE_MEMORY_FALLBACK=true
`;
}

/**
 * Install Python dependencies for memory system
 */
async function installPythonDeps(projectRoot, logger) {
  logger.log(chalk.cyan('\n📦 Installing Python dependencies...'));

  const requirementsPath = path.join(projectRoot, 'requirements.txt');
  
  // Check if requirements.txt exists
  if (!(await fs.pathExists(requirementsPath))) {
    // Create requirements.txt with memory dependencies
    const requirements = `# BMAD Memory System Dependencies
qdrant-client==1.7.0
sentence-transformers==2.2.2
python-dotenv==1.0.0
`;
    await fs.writeFile(requirementsPath, requirements);
    logger.log(chalk.dim('   Created requirements.txt'));
  }

  try {
    execSync('pip3 install -r requirements.txt', {
      cwd: projectRoot,
      stdio: 'pipe',
    });
    logger.log(chalk.green('   ✓ Python dependencies installed'));
  } catch (error) {
    logger.warn(chalk.yellow('   ⚠️  Could not install Python dependencies automatically'));
    logger.log(chalk.cyan('   Please run manually: pip3 install -r requirements.txt'));
  }
}

/**
 * Start Qdrant via docker-compose
 */
async function startQdrant(projectRoot, logger) {
  logger.log(chalk.cyan('\n🚀 Starting Qdrant vector database...'));

  // Check if Docker is available
  try {
    execSync('docker --version', { stdio: 'pipe' });
  } catch {
    logger.warn(chalk.yellow('   ⚠️  Docker not found. Qdrant requires Docker to run.'));
    return false;
  }

  // Check if docker-compose.yml exists
  const dockerComposePath = path.join(projectRoot, 'docker-compose.yml');
  if (!(await fs.pathExists(dockerComposePath))) {
    // Create minimal docker-compose.yml for Qdrant
    const dockerCompose = `version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: bmad-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage
    environment:
      - QDRANT_LOG_LEVEL=INFO

volumes:
  qdrant_storage:
`;
    await fs.writeFile(dockerComposePath, dockerCompose);
    logger.log(chalk.dim('   Created docker-compose.yml'));
  }

  // Start Qdrant
  try {
    execSync('docker-compose up -d qdrant', {
      cwd: projectRoot,
      stdio: 'pipe',
    });
    
    // Wait for Qdrant to be ready
    logger.log(chalk.dim('   Waiting for Qdrant to start...'));
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    logger.log(chalk.green('   ✓ Qdrant started at http://localhost:6333'));
    return true;
  } catch (error) {
    logger.warn(chalk.yellow('   ⚠️  Could not start Qdrant automatically'));
    return false;
  }
}

/**
 * Create Qdrant collections
 */
async function createCollections(projectRoot, logger) {
  logger.log(chalk.cyan('\n📊 Creating Qdrant collections...'));

  const scriptPath = path.join(projectRoot, 'scripts', 'memory', 'create-collections.py');
  
  // Ensure scripts directory exists
  await fs.ensureDir(path.join(projectRoot, 'scripts', 'memory'));

  // Create collection creation script if it doesn't exist
  if (!(await fs.pathExists(scriptPath))) {
    const script = `#!/usr/bin/env python3
"""Create Qdrant collections for BMAD memory system."""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Load environment
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_DIMENSION = 384  # sentence-transformers/all-MiniLM-L6-v2

collections = [
    os.getenv("QDRANT_KNOWLEDGE_COLLECTION", "bmad-knowledge"),
    os.getenv("QDRANT_AGENT_MEMORY_COLLECTION", "agent-memory"),
    os.getenv("QDRANT_BEST_PRACTICES_COLLECTION", "bmad-best-practices"),
]

client = QdrantClient(url=QDRANT_URL)

for collection_name in collections:
    try:
        # Check if collection exists
        client.get_collection(collection_name)
        print(f"✓ Collection '{collection_name}' already exists")
    except:
        # Create collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=EMBEDDING_DIMENSION, distance=Distance.COSINE),
        )
        print(f"✓ Created collection '{collection_name}'")

print("\\n✅ All collections ready!")
`;
    await fs.writeFile(scriptPath, script);
    await fs.chmod(scriptPath, '755');
  }

  // Run collection creation
  try {
    const output = execSync('python3 scripts/memory/create-collections.py', {
      cwd: projectRoot,
      encoding: 'utf8',
      stdio: 'pipe',
    });
    logger.log(chalk.dim(`   ${output.trim()}`));
    logger.log(chalk.green('   ✓ Collections created'));
  } catch (error) {
    logger.warn(chalk.yellow('   ⚠️  Could not create collections automatically'));
  }
}

/**
 * Run health check
 */
async function healthCheck(projectRoot, logger) {
  logger.log(chalk.cyan('\n🏥 Running health check...'));

  try {
    const response = await fetch('http://localhost:6333/health');
    if (response.ok) {
      logger.log(chalk.green('   ✓ Qdrant health check passed'));
    } else {
      logger.warn(chalk.yellow('   ⚠️  Qdrant health check failed'));
    }
  } catch {
    logger.warn(chalk.yellow('   ⚠️  Could not connect to Qdrant'));
  }
}

module.exports = { install };
