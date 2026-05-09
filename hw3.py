from helper_classes import *
import matplotlib.pyplot as plt

def get_normal(obj, point):
    """
    Helper function to get the normal vector of an object at a specific point.
    """
    if isinstance(obj, Sphere):
        # Normal of a sphere is the normalized vector from center to the surface point
        return normalize(point - obj.center)
    elif isinstance(obj, Plane) or isinstance(obj, Triangle):
        # Plane and Triangle have a constant normal
        return obj.normal
    return np.zeros(3)

def is_unblocked(intersection_point, normal, light, objects):
    """
    Checks if the path from the intersection point to the light source is unblocked (Shadow checking).
    """
    light_ray = light.get_light_ray(intersection_point)
    # The light_ray points from the light TO the surface, so we reverse it to get vector L
    L = normalize(-light_ray.direction)
    
    # Nudge the origin slightly along the normal to avoid self-intersection (Shadow Acne)
    shadow_origin = intersection_point + normal * epsilon
    shadow_ray = Ray(shadow_origin, L)
    
    hit_dist, hit_obj = shadow_ray.nearest_intersected_object(objects)
    dist_to_light = light.get_distance_from_light(intersection_point)
    
    # If the shadow ray hit something, and it's CLOSER than the light source, we are in shadow
    if hit_obj is not None and hit_dist < dist_to_light:
        return False
    return True

def get_diffuse_specular(intersection_point, normal, view_ray, light, obj):
    """
    Calculates the Diffuse and Specular components of the Phong reflection model.
    """
    light_ray = light.get_light_ray(intersection_point)
    L = normalize(-light_ray.direction) # Vector from surface to light
    N = normal
    V = normalize(-view_ray.direction)  # Vector from surface to camera
    
    intensity = light.get_intensity(intersection_point)
    
    # Diffuse Component
    n_dot_l = np.dot(N, L)
    if n_dot_l <= 0:
        return np.zeros(3) # Light is hitting the back of the surface
    
    diffuse = np.array(obj.diffuse) * n_dot_l * intensity
    
    # Specular Component
    # We use the reflected helper function. The incident ray is -L.
    R = normalize(reflected(-L, N))
    v_dot_r = np.dot(V, R)
    
    specular = np.zeros(3)
    if v_dot_r > 0:
        specular = np.array(obj.specular) * (v_dot_r ** obj.shininess) * intensity
        
    return diffuse + specular


def render_scene(camera, ambient, lights, objects, screen_size, max_depth):
    width, height = screen_size
    ratio = float(width) / height
    screen = (-1, 1 / ratio, 1, -1 / ratio)  # left, top, right, bottom

    image = np.zeros((height, width, 3))

    for i, y in enumerate(np.linspace(screen[1], screen[3], height)):
        for j, x in enumerate(np.linspace(screen[0], screen[2], width)):
            # screen is on origin
            pixel = np.array([x, y, 0])
            origin = camera
            direction = normalize(pixel - origin)
            ray = Ray(origin, direction)

            # Find nearest intersection
            min_distance, nearest_object = ray.nearest_intersected_object(objects)
            
            # If no intersection, color the pixel black
            if nearest_object is None:
                color = np.zeros(3)
            else:
                color = get_color(ambient, lights, objects, max_depth, ray, min_distance, nearest_object, 1)
            
            # Clip the values between 0 and 1
            image[i, j] = np.clip(color, 0, 1)

    return image


def get_color(ambient, lights, objects, max_depth, ray, min_distance, min_obj, depth):
    # Calculate the exact 3D intersection point
    intersection_point = ray.origin + min_distance * ray.direction
    normal = get_normal(min_obj, intersection_point)
    
    # Start with the Ambient Color
    color = np.array(ambient) * np.array(min_obj.ambient)
    
    # Add Diffuse & Specular from all unblocked light sources
    for light in lights:
        if is_unblocked(intersection_point, normal, light, objects):
            color += get_diffuse_specular(intersection_point, normal, ray, light, min_obj)
    
    # If we haven't reached the recursion limit, handle reflections and refractions
    if depth < max_depth:
        # Reflection
        if min_obj.reflection > 0:
            reflect_dir = normalize(reflected(ray.direction, normal))
            # Nudge origin outside to prevent self-intersection
            reflect_origin = intersection_point + normal * epsilon
            reflect_ray = Ray(reflect_origin, reflect_dir)
            
            r_dist, r_obj = reflect_ray.nearest_intersected_object(objects)
            if r_obj is not None:
                r_color = get_color(ambient, lights, objects, max_depth, reflect_ray, r_dist, r_obj, depth + 1)
                color += r_color * min_obj.reflection

        # Refraction (Scene 6) - Using dynamic transparency attribute if it exists
        transparency = getattr(min_obj, "transparency", 0)
        if transparency > 0:
            # Nudge origin INSIDE the object
            refract_origin = intersection_point - normal * epsilon 
            # Relaxed version: ray continues in the exact same direction
            refract_ray = Ray(refract_origin, ray.direction)
            
            t_dist, t_obj = refract_ray.nearest_intersected_object(objects)
            if t_obj is not None:
                t_color = get_color(ambient, lights, objects, max_depth, refract_ray, t_dist, t_obj, depth + 1)
                # Blend the current color and the refracted color
                color = color * (1 - transparency) + t_color * transparency

    return color


def your_own_scene():
    # Fixed parameters: set_material takes exactly 5 parameters. Transparency is added dynamically.
    bubble_a = Sphere([-0.5, 0, -0.5], 0.45)
    bubble_a.set_material([0.05, 0.05, 0.025], [0.05, 0.05, 0.025], [0.1, 0.1, 0.1], 100, 0.7)
    bubble_a.transparency = 0.9  # Set transparency directly for scene 6 logic
    
    bubble_b = Sphere([0.5, 0, -0.5], 0.45)
    bubble_b.set_material([0.05, 0.05, 0.025], [0.05, 0.05, 0.025], [0.1, 0.1, 0.1], 100, 0.7)
    bubble_b.transparency = 0.9

    plane_a = Plane([0, 1, 0], [0, -1, 0])
    plane_a.set_material([0.7, 0.2, 0.35], [0.7, 0.2, 0.35], [1, 1, 1], 10, 0.5)
    
    plane_b = Plane([0, 0, 1], [0, 0, -3])
    plane_b.set_material([0.7, 0.36, 0.38], [0.7, 0.36, 0.38], [1, 1, 1], 10, 0.5)

    objects = [bubble_a, bubble_b, plane_a, plane_b]

    # add the 2 lights sources
    p_light = PointLight(intensity=np.array([1, 1, 1]), position=np.array([0, 1, 1]), kc=0.1, kl=0.1, kq=0.1)
    d_light = DirectionalLight(intensity=np.array([1, 1, 0.56]), direction=np.array([1, 1, 1]))
    lights = [p_light, d_light]

    camera = np.array([0, 0, 1])
    return camera, lights, objects