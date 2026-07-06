import com.android.build.api.dsl.LibraryExtension

val libraryNamespaces =
    mapOf(
        "geofence_service" to "com.pravera.geofence_service",
        "fl_location" to "com.pravera.fl_location",
        "flutter_activity_recognition" to "com.pravera.flutter_activity_recognition",
        "flutter_foreground_task" to "com.pravera.flutter_foreground_task",
        "share_plus" to "dev.fluttercommunity.plus.share",
        "usage_stats" to "io.github.parassharmaa.usage_stats",
    )

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}

subprojects {
    plugins.withId("com.android.library") {
        extensions.configure<LibraryExtension>("android") {
            compileSdk = 35
            if (namespace == null) {
                namespace =
                    libraryNamespaces[project.name]
                        ?: "com.example.nh_reminder.${project.name.replace(Regex("[^A-Za-z0-9_]"), "_")}"
            }
        }
    }
}

subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
